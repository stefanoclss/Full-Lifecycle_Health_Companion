from .base import CareStageStrategy

class MonitoringStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "📉 Continuous Monitoring",
            "description": "Patient Vitals & Recovery",
            "content": [
               {
                   "type": "chart",
                   "chart_type": "line",
                   "label": "Recovery Trajectory",
                   "data": [
                       {"x": 1, "y": 80},
                       {"x": 2, "y": 70},
                       {"x": 3, "y": 40},
                       {"x": 4, "y": 30},
                       {"x": 5, "y": 10}
                   ],
                   "color": "#64FFDA"
               },
               {"type": "text", "text": "Recovery Trajectory: On Track", "style": "success"}
            ]
        }

    def process_action(self, data: dict) -> dict:
        return {"status": "success", "data": "Refresh complete"}
