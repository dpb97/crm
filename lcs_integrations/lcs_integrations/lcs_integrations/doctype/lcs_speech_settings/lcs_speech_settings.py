import frappe
from frappe.model.document import Document


class LCSSpeechSettings(Document):
    def on_update(self):
        """Invalidate any cached Azure token when settings change
        (key rotation, region switch)."""
        # Clear all azure_speech_token:* cache keys; no-op if none exist
        try:
            frappe.cache().delete_keys("azure_speech_token:")
        except Exception:
            pass
