import { Component, computed, inject } from '@angular/core';
import { RosaryStateService } from '../../services/rosary-state';
import { LanguageService } from '../../services/language';

const CX = 280,
  CY = 270,
  RX = 218,
  RY = 208;
const TOTAL = 55; // 5 decades × 11 beads (1 Our Father + 10 Hail Mary)
const DEC_SIZE = 11;

interface BeadData {
  index: number;
  cx: number;
  cy: number;
  r: number;
  isOurFather: boolean;
  decadeNumber: number | null;
}

function beadPos(i: number): { x: number; y: number } {
  const angle = (i / TOTAL) * 2 * Math.PI - Math.PI / 2;
  return { x: CX + RX * Math.cos(angle), y: CY + RY * Math.sin(angle) };
}

export const BEADS: BeadData[] = Array.from({ length: TOTAL }, (_, i) => {
  const { x, y } = beadPos(i);
  const isOF = i % DEC_SIZE === 0;
  return {
    index: i,
    cx: x,
    cy: y,
    r: isOF ? 13 : 7,
    isOurFather: isOF,
    decadeNumber: isOF ? Math.floor(i / DEC_SIZE) + 1 : null,
  };
});

@Component({
  selector: 'app-rosary-visualizer',
  imports: [],
  templateUrl: './rosary-visualizer.html',
  styleUrl: './rosary-visualizer.scss',
})
export class RosaryVisualizer {
  private readonly stateService = inject(RosaryStateService);
  private readonly languageService = inject(LanguageService);

  readonly CX = CX;
  readonly CY = CY;
  readonly RX = RX;
  readonly RY = RY;
  readonly beads = BEADS;

  readonly svgAriaLabel = computed(() =>
    this.languageService.t('svg_label'),
  );
  readonly svgTitle = computed(() => this.languageService.t('svg_title'));
  readonly legendCurrent = computed(() =>
    this.languageService.t('current_bead'),
  );
  readonly legendOurFather = computed(() =>
    this.languageService.t('our_father'),
  );
  readonly legendHailMary = computed(() =>
    this.languageService.t('hail_mary'),
  );
  readonly legendCompleted = computed(() =>
    this.languageService.t('completed'),
  );

  private activeIndex = computed<number>(() => {
    const s = this.stateService.state();
    if (!s || s.decade === 0) return -1;
    return (s.decade - 1) * DEC_SIZE + s.bead;
  });

  beadFill(bead: BeadData): string {
    const ai = this.activeIndex();
    if (bead.index === ai) return '#ffd700';
    const s = this.stateService.state();
    if (s && s.completed_decades.includes(this.beadDecade(bead.index))) {
      return '#777';
    }
    return bead.isOurFather ? '#5c2d1e' : '#8b6914';
  }

  beadStroke(bead: BeadData): string {
    const ai = this.activeIndex();
    if (bead.index === ai) return '#c8960c';
    const s = this.stateService.state();
    if (s && s.completed_decades.includes(this.beadDecade(bead.index))) {
      return '#555';
    }
    return '#3a2a0a';
  }

  beadStrokeWidth(bead: BeadData): number {
    return this.activeIndex() === bead.index ? 3 : 1.5;
  }

  beadRadius(bead: BeadData): number {
    const ai = this.activeIndex();
    if (bead.index === ai) return bead.isOurFather ? 17 : 11;
    return bead.r;
  }

  isActive(bead: BeadData): boolean {
    return this.activeIndex() === bead.index;
  }

  private beadDecade(i: number): number {
    return Math.floor(i / DEC_SIZE) + 1;
  }
}
