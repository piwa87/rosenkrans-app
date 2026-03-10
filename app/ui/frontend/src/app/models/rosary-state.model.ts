/** Mirrors the Python RosaryState.to_dict() output. */
export interface RosaryState {
  decade: number;
  bead: number;
  state: 'IDLE' | 'OUR_FATHER' | 'HAIL_MARY' | 'GLORY_BE' | 'COMPLETE';
  completed_decades: number[];
  last_prayer: string | null;
}

export interface Translations {
  [key: string]: string;
}

export interface TranslationMap {
  [lang: string]: Translations;
}

export const UI_TRANSLATIONS: TranslationMap = {
  en: {
    page_title: 'Rosary Progress Tracker',
    title: '🙏 Rosary Progress Tracker',
    language_label: 'Language',
    svg_label: 'Rosary bead tracker',
    svg_title: 'Rosary bead progress tracker',
    waiting: '🙏 Waiting for prayer…',
    current_bead: 'Current bead',
    our_father: 'Our Father',
    hail_mary: 'Hail Mary',
    completed: 'Completed',
    decade: 'Decade {number}',
    status_our_father: '✝️  Decade {decade} — Our Father',
    status_hail_mary: '📿 Decade {decade} — Hail Mary {bead} / 10',
    status_glory_be: '✨ Decade {decade} — Glory Be ✓',
    status_complete: '🎉 Rosary Complete! God bless you.',
    bead_count: 'Bead {bead} of 10',
  },
  da: {
    page_title: 'Rosenkrans-fremskridt',
    title: '🙏 Rosenkrans-fremskridt',
    language_label: 'Sprog',
    svg_label: 'Oversigt over rosenkransens perler',
    svg_title: 'Rosenkransens perleoversigt',
    waiting: '🙏 Venter på bøn…',
    current_bead: 'Nuværende perle',
    our_father: 'Fadervor',
    hail_mary: 'Hil dig, Maria',
    completed: 'Fuldført',
    decade: 'Dekade {number}',
    status_our_father: '✝️  Dekade {decade} — Fadervor',
    status_hail_mary: '📿 Dekade {decade} — Hil dig, Maria {bead} / 10',
    status_glory_be: '✨ Dekade {decade} — Ære være Faderen ✓',
    status_complete: '🎉 Rosenkransen er fuldført! Gud velsigne dig.',
    bead_count: 'Perle {bead} af 10',
  },
};

export const SUPPORTED_LANGUAGES: { [code: string]: string } = {
  en: 'English',
  da: 'Dansk',
};
