import { Component, computed, inject } from '@angular/core';
import { RosaryStateService } from '../../services/rosary-state';
import { LanguageService } from '../../services/language';

@Component({
  selector: 'app-status-panel',
  imports: [],
  templateUrl: './status-panel.html',
  styleUrl: './status-panel.scss',
})
export class StatusPanel {
  private readonly stateService = inject(RosaryStateService);
  private readonly languageService = inject(LanguageService);

  readonly decades = [1, 2, 3, 4, 5];

  readonly statusText = computed(() => {
    const s = this.stateService.state();
    const t = (k: string, v?: Record<string, string | number>) =>
      this.languageService.t(k, v);
    if (!s) return t('waiting');
    const map: Record<string, string> = {
      IDLE: t('waiting'),
      OUR_FATHER: t('status_our_father', { decade: s.decade }),
      HAIL_MARY: t('status_hail_mary', { decade: s.decade, bead: s.bead }),
      GLORY_BE: t('status_glory_be', { decade: s.decade }),
      COMPLETE: t('status_complete'),
    };
    return map[s.state] ?? s.state;
  });

  readonly beadCountText = computed(() => {
    const s = this.stateService.state();
    if (!s || s.state !== 'HAIL_MARY') return '';
    return this.languageService.t('bead_count', { bead: s.bead });
  });

  decadeTitle(d: number): string {
    return this.languageService.t('decade', { number: d });
  }

  decadeClass(d: number): string {
    const s = this.stateService.state();
    if (!s) return 'decade-dot';
    if (s.completed_decades.includes(d)) return 'decade-dot done';
    if (d === s.decade) return 'decade-dot active';
    return 'decade-dot';
  }
}
