import frappe
from frappe.model.document import Document


class LCSOpportunityMatrix(Document):
    def validate(self):
        self.calculate_score()
        self.determine_classification()
        self.determine_activity_level()
        self.update_project_probability()

    def calculate_score(self):
        weights = {
            "technical_fit": 0.25,
            "commercial_fit": 0.25,
            "relationship_strength": 0.20,
            "competition_level": 0.15,
            "strategic_importance": 0.15,
        }
        total = sum(
            (getattr(self, field, 0) or 0) * weight
            for field, weight in weights.items()
        )
        self.total_score = round(total, 1)
        self.weighted_probability = round(total * 0.9, 1)  # slight discount

    def determine_classification(self):
        score = self.total_score or 0
        if score >= 80:
            self.classification = "Order"
        elif score >= 60:
            self.classification = "Negotiation"
        elif score >= 40:
            self.classification = "Offer"
        elif score >= 20:
            self.classification = "Inquiry"
        else:
            self.classification = "Pre-Project"

    def determine_activity_level(self):
        score = self.total_score or 0
        if score >= 75:
            self.activity_level = 4
        elif score >= 50:
            self.activity_level = 3
        elif score >= 25:
            self.activity_level = 2
        else:
            self.activity_level = 1

    def update_project_probability(self):
        if self.project:
            frappe.db.set_value(
                "LCS Project", self.project, "probability", self.weighted_probability
            )
