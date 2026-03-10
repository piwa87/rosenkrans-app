import { Component, OnInit, computed, effect, inject } from '@angular/core';
import { RosaryStateService } from './services/rosary-state';
import { LanguageService } from './services/language';
import { StatusPanel } from './components/status-panel/status-panel';
import { RosaryVisualizer } from './components/rosary-visualizer/rosary-visualizer';
import { LanguageSelector } from './components/language-selector/language-selector';

@Component({
  selector: 'app-root',
  imports: [StatusPanel, RosaryVisualizer, LanguageSelector],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private readonly stateService = inject(RosaryStateService);
  private readonly languageService = inject(LanguageService);

  readonly title = computed(() => this.languageService.t('title'));

  constructor() {
    // Keep <html lang="..."> in sync with chosen language
    effect(() => {
      document.documentElement.lang = this.languageService.language();
      document.title = this.languageService.t('page_title');
    });
  }

  ngOnInit(): void {
    this.stateService.connect();
  }
}
