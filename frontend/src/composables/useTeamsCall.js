/**
 * useTeamsCall — start a Microsoft Teams call and log it as a CRM Call Log.
 *
 * Replaces the Twilio/Exotel dialer: "calling" a contact opens a Teams call
 * (VoIP by e-mail, PSTN by number via Teams Phone) and records the attempt
 * so it appears in the Calls tab / Call Logs with medium "Teams".
 */
import { call, toast } from 'frappe-ui'

export function useTeamsCall() {
  /**
   * @param {Object} opts
   * @param {string} [opts.email]  Teams user e-mail → VoIP call (preferred)
   * @param {string} [opts.phone]  phone number → PSTN call (needs Teams Phone)
   * @param {string} [opts.reference_doctype]
   * @param {string} [opts.reference_name]
   */
  async function teamsCall({ email, phone, reference_doctype, reference_name } = {}) {
    if (!email && !phone) {
      toast.error(__('No phone number or Teams address for this contact.'))
      return null
    }
    try {
      const res = await call('lcs_integrations.teams.calling.start_teams_call', {
        email: email || null,
        phone: phone || null,
        reference_doctype: reference_doctype || null,
        reference_name: reference_name || null,
      })
      if (res?.url) window.open(res.url, '_blank', 'noopener')
      toast.success(__('Teams call started — logged in Call Logs.'))
      return res
    } catch (e) {
      toast.error(e?.messages?.[0] || __('Could not start the Teams call.'))
      return null
    }
  }

  return { teamsCall }
}
