// Shared phone-country helpers: derive a country (flag + dial) from a phone
// number's international "+<dial>" prefix. Used by PhoneInput (create forms)
// and PrimaryDropdown / PrimaryDropdownItem (contact detail phone dropdown).
//
// Country NAMES come from Intl.DisplayNames; FLAGS from flag-icons classes
// (emoji flags don't render on Windows). Only [iso2, dial] pairs are hand-kept.

// Shared dial codes list the primary first (used for prefix detection).
const RAW = [
  ['AT', 43], ['DE', 49], ['CH', 41], ['LI', 423], ['IT', 39], ['FR', 33],
  ['ES', 34], ['PT', 351], ['GB', 44], ['IE', 353], ['NL', 31], ['BE', 32],
  ['LU', 352], ['DK', 45], ['SE', 46], ['NO', 47], ['FI', 358], ['IS', 354],
  ['PL', 48], ['CZ', 420], ['SK', 421], ['HU', 36], ['SI', 386], ['HR', 385],
  ['BA', 387], ['RS', 381], ['ME', 382], ['MK', 389], ['AL', 355], ['GR', 30],
  ['BG', 359], ['RO', 40], ['MD', 373], ['UA', 380], ['BY', 375], ['LT', 370],
  ['LV', 371], ['EE', 372], ['RU', 7], ['KZ', 7], ['TR', 90], ['CY', 357],
  ['MT', 356], ['US', 1], ['CA', 1], ['MX', 52], ['BR', 55], ['AR', 54],
  ['CL', 56], ['CO', 57], ['PE', 51], ['CN', 86], ['JP', 81], ['KR', 82],
  ['IN', 91], ['ID', 62], ['TH', 66], ['VN', 84], ['SG', 65], ['MY', 60],
  ['PH', 63], ['AU', 61], ['NZ', 64], ['ZA', 27], ['EG', 20], ['MA', 212],
  ['NG', 234], ['KE', 254], ['IL', 972], ['SA', 966], ['AE', 971], ['QA', 974],
]

const regionNames = (() => {
  try {
    return new Intl.DisplayNames(['de'], { type: 'region' })
  } catch {
    return null
  }
})()

export const COUNTRIES = RAW.map(([iso2, dial]) => ({
  iso2,
  dial,
  name: (regionNames && regionNames.of(iso2)) || iso2,
})).sort((a, b) => a.name.localeCompare(b.name, 'de'))

// Detection order: longest dial wins; equal dial → the primary (first in RAW).
const BY_LEN = [...COUNTRIES].sort(
  (a, b) =>
    String(b.dial).length - String(a.dial).length ||
    RAW.findIndex((r) => r[0] === a.iso2) - RAW.findIndex((r) => r[0] === b.iso2),
)

// Return the country for a phone value's "+<dial>" prefix, or null (also null
// for non-phone strings like e-mails, since they don't start with '+').
export function detectCountry(value) {
  const s = String(value || '').trim()
  if (!s.startsWith('+')) return null
  const d = s.slice(1).replace(/\D/g, '')
  if (!d) return null
  for (const c of BY_LEN) {
    if (d.startsWith(String(c.dial))) return c
  }
  return null
}

// flag-icons classes for an ISO2 code, or [] when unknown.
export function flagClass(iso2) {
  return iso2 ? ['fi', 'fi-' + String(iso2).toLowerCase()] : []
}
