import os
import traceback
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")

MODEL_PATHS = {
    "triage_edge": os.path.join(MODELS_DIR, "gguf", "gemma-2-2b-it-Q4_K_M.gguf"),
    "intake_chat": os.path.join(MODELS_DIR, "medgemma-1.5-4b-it"),
    "consult_reasoning": os.path.join(MODELS_DIR, "medgemma-1.5-4b-it"),
    "cxr_foundation": os.path.join(MODELS_DIR, "cxr-foundation"),
    "medasr": os.path.join(MODELS_DIR, "medasr"),
}

class ModelRegistry:
    _model_cache = {}
    _tokenizer_cache = {}

    # ==================================================================
    # CTC Decoding Helper
    # ==================================================================

    @staticmethod
    def _decode_ctc_greedy(processor, logits):
        """
        Manually implement greedy CTC decoding:
        1. Argmax logits
        2. Remove adjacent duplicates
        3. remove blank token (id 0 or pad_token_id)
        4. Decode
        """
        import torch
        predicted_ids = torch.argmax(logits, dim=-1)
        
        # Get blank token ID - usually pad_token_id or 0 for CTC models
        blank_id = processor.tokenizer.pad_token_id
        if blank_id is None:
            blank_id = 0 # Default for many speech models

        decoded_sequences = []
        for sequence in predicted_ids:
            unique_ids = []
            prev_id = -1
            for t_id in sequence:
                t_id = t_id.item()
                if t_id != prev_id:
                    unique_ids.append(t_id)
                    prev_id = t_id
            
            # Filter blanks
            filtered_ids = [tid for tid in unique_ids if tid != blank_id]
            
            # Decode using processor (it handles special tokens better usually)
            text = processor.decode(filtered_ids, skip_special_tokens=True)
            # Extra cleanup for 'epsilon' if it leaks (rare with skip_special_tokens=True but possible if mapped to normal token)
            text = text.replace("<epsilon>", "").replace("<s>", "").replace("</s>", "").strip()
            decoded_sequences.append(text)
            
        return decoded_sequences[0] if decoded_sequences else ""

    # ==================================================================
    # Model Path / Availability
    # ==================================================================

    @staticmethod
    def get_model_path(role):
        return MODEL_PATHS.get(role)

    @staticmethod
    def is_model_available(role):
        path = MODEL_PATHS.get(role)
        return path and os.path.exists(path)

    # ==================================================================
    # General Inference (MedGemma, Gemma, etc.)
    # ==================================================================

    @staticmethod
    def run_inference(role, prompt):
        path = ModelRegistry.get_model_path(role)

        if path and os.path.exists(path):
            try:
                if role == "triage_edge" and path.endswith(".gguf"):
                    try:
                        from llama_cpp import Llama
                        pass
                    except ImportError:
                        print(f"Warning: 'llama-cpp-python' not installed. Cannot run {role} model.")

                elif os.path.isdir(path):
                    try:
                        import torch
                        from transformers import AutoModelForCausalLM, AutoTokenizer

                        print(f"Loading model from {path}...")
                        device = "cuda" if torch.cuda.is_available() else "cpu"
                        torch_dtype = torch.float16 if device == "cuda" else torch.float32

                        tokenizer = AutoTokenizer.from_pretrained(path)
                        model = AutoModelForCausalLM.from_pretrained(
                            path,
                            torch_dtype=torch_dtype,
                            device_map=device,
                            low_cpu_mem_usage=True,
                        )

                        # FIX 2: Use actual model context limit instead of hardcoded 1024
                        model_max_ctx = getattr(model.config, "max_position_embeddings", 4096)

                        # FIX 5: Truncate input to always leave room for generation
                        inputs = tokenizer(
                            prompt,
                            return_tensors="pt",
                            truncation=True,
                            max_length=model_max_ctx - 256,
                        ).to(device)

                        input_length = inputs.input_ids.shape[1]
                        max_new_tokens = min(256, model_max_ctx - input_length)

                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=max_new_tokens,
                            do_sample=False,
                        )

                        generated_tokens = outputs[0][input_length:]
                        return tokenizer.decode(generated_tokens, skip_special_tokens=True)

                    except ImportError:
                        print(f"Warning: 'transformers' or 'torch' not installed. Cannot run {role} model.")
                    except Exception as e:
                        print(f"Error during inference: {e}")

            except Exception as e:
                print(f"Error running model {role}: {e}")

        if role == "triage_edge":
            return "(Edge AI - Gemma 2B) Based on symptoms, suggested priority: Level 2."
        elif role == "intake_chat":
            return "(Intake AI - TxGemma 2B) Patient history noted. Generating SOAP..."
        elif role == "consult_reasoning":
            return "(Consult AI - MedGemma 1.5 4B) Analysis complete. Differential diagnosis suggestions ready."
        return "AI Service Unavailable."

    # ==================================================================
    # Choice Probabilities (MedGemma logprobs)
    # ==================================================================

    @staticmethod
    def compute_choice_probabilities(role, prompt, choices):
        """
        Calculates the probability of specific choice tokens given a prompt.
        Returns a dictionary {choice: probability}.
        Currently only implemented for 'transformers' backend.
        """
        path = ModelRegistry.get_model_path(role)

        # Fallback if model not found
        if not path or not os.path.exists(path):
            return {c: 1.0/len(choices) for c in choices}

        try:
            # 1. Handle Full Models (Transformers)
            if os.path.isdir(path):
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch.nn.functional as F

                device = "cuda" if torch.cuda.is_available() else "cpu"
                torch_dtype = torch.float16 if device == "cuda" else torch.float32

                # Check cache
                if path in ModelRegistry._model_cache:
                    # print(f"Using cached model from {path}...")
                    model = ModelRegistry._model_cache[path]
                    tokenizer = ModelRegistry._tokenizer_cache[path]
                else:
                    print(f"Loading model for logprobs from {path}...")
                    tokenizer = AutoTokenizer.from_pretrained(path)
                    model = AutoModelForCausalLM.from_pretrained(
                        path,
                        torch_dtype=torch_dtype,
                        device_map=device,
                        low_cpu_mem_usage=True,
                    )
                    model.eval()
                    ModelRegistry._model_cache[path] = model
                    ModelRegistry._tokenizer_cache[path] = tokenizer

                # Pre-tokenize prompt
                prompt_inputs = tokenizer(prompt, return_tensors="pt").to(device)
                
                choice_scores = []
                
                with torch.no_grad():
                    # We want P(choice | prompt). 
                    # Efficient approach: Get logits for the LAST token of the prompt.
                    outputs = model(**prompt_inputs)
                    next_token_logits = outputs.logits[0, -1, :] # [vocab_size]
                    
                    for choice in choices:
                        # Encode choice without special tokens to get the ID
                        # Note: we assume choices are single tokens or we take the first token
                        choice_ids = tokenizer.encode(choice, add_special_tokens=False)
                        if not choice_ids:
                            choice_scores.append(-float('inf'))
                            continue
                            
                        first_token_id = choice_ids[0]
                        score = next_token_logits[first_token_id].item()
                        choice_scores.append(score)

                # Softmax over the selected choices
                scores_tensor = torch.tensor(choice_scores)
                probs = F.softmax(scores_tensor, dim=0).tolist()
                
                return {choice: round(p, 4) for choice, p in zip(choices, probs)}

        except Exception as e:
            print(f"Error computing probabilities: {e}")
            pass

        return {c: 1.0/len(choices) for c in choices}

    # ==================================================================
    # MedASR Audio Transcription
    # ==================================================================
    #
    # MedASR is a Conformer-based CTC model from Google Health AI.
    # It requires: mono-channel audio, 16kHz, float32 waveform.
    #
    # Official transformers requirement: >= 5.0.0 from specific commit:
    #   pip install git+https://github.com/huggingface/transformers.git@65dc261512cbdb1ee72b88ae5b222f2605aad8e5
    #
    # Three independent fallback stages:
    #   1. Pipeline (cleanest, needs correct transformers)
    #   2. Direct inference via AutoModelForCTC + processor
    #   3. Manual torchaudio fbank features (bypasses LasrFeatureExtractor)
    # ==================================================================

    @staticmethod
    def _load_audio(audio_path, target_sr=16000):
        """
        Load audio file to float32 numpy array at target sample rate.
        Tries librosa -> pydub -> soundfile in order.
        """
        # --- Try librosa (cleanest, used by official MedASR examples) ---
        try:
            import librosa
            speech, _ = librosa.load(audio_path, sr=target_sr, mono=True)
            print(f"[MedASR] Audio loaded with librosa: shape={speech.shape}")
            return speech.astype(np.float32)
        except Exception as e:
            print(f"[MedASR] librosa failed: {e}")

        # --- Try pydub (uses ffmpeg via PATH) ---
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_frame_rate(target_sr).set_channels(1)
            samples = np.array(audio.get_array_of_samples())
            if audio.sample_width == 2:
                speech = samples.astype(np.float32) / 32768.0
            elif audio.sample_width == 4:
                speech = samples.astype(np.float32) / 2147483648.0
            else:
                speech = samples.astype(np.float32)
            print(f"[MedASR] Audio loaded with pydub: shape={speech.shape}")
            return speech
        except Exception as e:
            print(f"[MedASR] pydub failed: {e}")

        # --- Try soundfile + torchaudio resample ---
        try:
            import soundfile as sf
            import torch
            import torchaudio
            audio, sr = sf.read(audio_path, dtype="float32")
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            if sr != target_sr:
                waveform = torch.from_numpy(audio).unsqueeze(0)
                resampler = torchaudio.transforms.Resample(sr, target_sr)
                waveform = resampler(waveform)
                audio = waveform.squeeze(0).numpy()
            print(f"[MedASR] Audio loaded with soundfile: shape={audio.shape}")
            return audio.astype(np.float32)
        except Exception as e:
            print(f"[MedASR] soundfile failed: {e}")

        raise RuntimeError(f"Could not load audio from {audio_path} with any backend.")

    @staticmethod
    def _medasr_try_pipeline(model_path, speech, device):
        """Stage 1: HuggingFace pipeline with pre-loaded audio."""
        try:
            from transformers import pipeline
            print("[MedASR] Stage 1: Trying pipeline approach...")

            transcriber = pipeline(
                "automatic-speech-recognition",
                model=model_path,
                device=device,
                chunk_length_s=20,
            )

            result = transcriber(
                {"raw": speech, "sampling_rate": 16000},
                stride_length_s=2,
            )

            text = result.get("text", "").strip()
            if text:
                print(f"[MedASR] Pipeline succeeded: '{text[:80]}...'")
                return text
            print("[MedASR] Pipeline returned empty text.")
            return None
        except Exception as e:
            print(f"[MedASR] Pipeline failed: {e}")
            traceback.print_exc()
            return None

    @staticmethod
    def _medasr_try_direct(model_path, speech, device):
        """
        Stage 2: Direct model inference using official MedASR approach.
        Uses AutoModelForCTC + AutoProcessor + model.generate().
        """
        try:
            from transformers import AutoModelForCTC, AutoProcessor
            import torch
            print("[MedASR] Stage 2: Trying direct inference (processor + generate)...")

            processor = AutoProcessor.from_pretrained(model_path)
            model = AutoModelForCTC.from_pretrained(model_path).to(device)
            model.eval()

            inputs = processor(
                speech,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True,
            )
            inputs = inputs.to(device)

            with torch.no_grad():
                # model.generate() handles decoding properly
                try:
                    outputs = model.generate(**inputs)
                    text = processor.batch_decode(outputs)[0].strip()
                except (AttributeError, TypeError):
                    # Some CTC models don't have generate(); greedy fallback
                    print("[MedASR] model.generate() unavailable, using greedy decode...")
                    logits = model(**inputs).logits
                    text = ModelRegistry._decode_ctc_greedy(processor, logits)

            if text:
                print(f"[MedASR] Direct inference succeeded: '{text[:80]}...'")
                return text
            print("[MedASR] Direct inference returned empty text.")
            return None
        except Exception as e:
            print(f"[MedASR] Direct inference failed: {e}")
            traceback.print_exc()
            return None

    @staticmethod
    def _medasr_try_manual_features(model_path, speech, device):
        """
        Stage 3: Bypass LasrFeatureExtractor entirely.
        Manually compute 128-dim fbank features with torchaudio, then feed
        input_features directly to the model.

        This fixes: 'LasrFeatureExtractor._torch_extract_fbank_features()
        takes from 2 to 3 positional arguments but 4 were given'
        """
        try:
            from transformers import AutoModelForCTC, AutoProcessor
            import torch
            import torchaudio
            print("[MedASR] Stage 3: Manual feature extraction (bypassing LasrFeatureExtractor)...")

            processor = AutoProcessor.from_pretrained(model_path)
            model = AutoModelForCTC.from_pretrained(model_path).to(device)
            model.eval()

            # ── Chunk long audio: 20s chunks, 2s overlap ─────────────
            chunk_samples = 20 * 16000    # 20 seconds
            stride_samples = 2 * 16000    # 2 seconds overlap
            step = chunk_samples - stride_samples
            total_samples = len(speech)

            if total_samples <= chunk_samples:
                chunks = [speech]
            else:
                chunks = []
                start = 0
                while start < total_samples:
                    end = min(start + chunk_samples, total_samples)
                    chunks.append(speech[start:end])
                    if end >= total_samples:
                        break
                    start += step

            print(f"[MedASR] Processing {len(chunks)} chunk(s)...")
            all_texts = []

            for i, chunk in enumerate(chunks):
                # ── Extract 128-dim fbank features ────────────────────
                waveform = torch.from_numpy(chunk).float()
                if waveform.dim() == 1:
                    waveform = waveform.unsqueeze(0)  # (1, time)

                features = torchaudio.compliance.kaldi.fbank(
                    waveform,
                    num_mel_bins=128,
                    sample_frequency=16000,
                    frame_length=25.0,
                    frame_shift=10.0,
                )
                # features shape: (num_frames, 128)

                # Utterance-level CMVN normalization
                features = features - features.mean(dim=0, keepdim=True)
                features = features / (features.std(dim=0, keepdim=True) + 1e-6)

                # Add batch dim: (1, num_frames, 128) and send to device
                input_features = features.unsqueeze(0).to(device)

                with torch.no_grad():
                    logits = model(input_features=input_features).logits

                chunk_text = ModelRegistry._decode_ctc_greedy(processor, logits)
                if chunk_text.strip():
                    all_texts.append(chunk_text.strip())
                    print(f"[MedASR]   Chunk {i+1}/{len(chunks)}: '{chunk_text.strip()[:60]}...'")

            text = " ".join(all_texts).strip()
            if text:
                print(f"[MedASR] Manual features succeeded: '{text[:80]}...'")
                return text
            print("[MedASR] Manual features returned empty text.")
            return None
        except Exception as e:
            print(f"[MedASR] Manual feature extraction failed: {e}")
            traceback.print_exc()
            return None

    @staticmethod
    def transcribe_audio(role, audio_path):
        """
        Transcribes audio file using Google MedASR.

        Three independent fallback stages:
          1. Pipeline (cleanest — needs transformers >= 5.0.0)
          2. Direct inference (AutoModelForCTC + processor + generate)
          3. Manual torchaudio fbank features (bypasses broken LasrFeatureExtractor)

        Returns dict with:
          - "text": Full transcription string
          - "segments": List of segment dicts [{text, timestamp}, ...]
        """
        path = ModelRegistry.get_model_path(role)
        if not path or not os.path.exists(path):
            return {"text": "ASR Model not found.", "segments": []}

        if not os.path.exists(audio_path):
            return {"text": f"Audio file not found: {audio_path}", "segments": []}

        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[MedASR] Device: {device}, Model: {path}")

        # ── Load audio (independent of model code — avoids torchcodec) ──
        try:
            speech = ModelRegistry._load_audio(audio_path, target_sr=16000)
        except Exception as e:
            return {"text": f"Error loading audio: {e}", "segments": []}

        # ── Stage 1: Pipeline ───────────────────────────────────────────
        text = ModelRegistry._medasr_try_pipeline(path, speech, device)
        if text:
            return {"text": text, "segments": [{"text": text, "timestamp": (0.0, None)}]}

        # ── Stage 2: Direct inference ───────────────────────────────────
        text = ModelRegistry._medasr_try_direct(path, speech, device)
        if text:
            return {"text": text, "segments": [{"text": text, "timestamp": (0.0, None)}]}

        # ── Stage 3: Manual features (bypasses LasrFeatureExtractor) ────
        text = ModelRegistry._medasr_try_manual_features(path, speech, device)
        if text:
            return {"text": text, "segments": [{"text": text, "timestamp": (0.0, None)}]}

        return {"text": "Transcription failed at all stages.", "segments": []}