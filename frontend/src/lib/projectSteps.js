// Canonical project-workspace steps — shared by the project page (which renders
// the panes) and the shell sidebar (which shows these steps INSTEAD of the main
// Vertrieb menu while a project is open). `slug` is the stable URL key
// (?step=), `t` is the LCSProject T.* key its activeTab uses, `label` is the
// display text (run through __()), `icon` a PpSidebar icon name.
export const PROJECT_STEPS = [
  { slug: 'overview',     t: 'OV',   label: 'Overview',        icon: 'grid' },
  { slug: 'engineering',  t: 'MTX',  label: 'Projektierung',   icon: 'compass' },
  { slug: 'calculation',  t: 'KALK', label: 'Calculation',     icon: 'dollar-sign' },
  { slug: 'offers',       t: 'OFF',  label: 'Offers',          icon: 'file-text' },
  { slug: 'negotiations', t: 'ACT',  label: 'Verhandlungen',   icon: 'calendar' },
  { slug: 'handover',     t: 'EXE',  label: 'Projektübergabe', icon: 'award' },
  { slug: 'contacts',     t: 'CON',  label: 'Contacts',        icon: 'users' },
  { slug: 'documents',    t: 'DOC',  label: 'Documents',       icon: 'folder' },
]
