import { Component, computed, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LanguageService } from '../../services/language';

@Component({
  selector: 'app-language-selector',
  imports: [FormsModule],
  templateUrl: './language-selector.html',
  styleUrl: './language-selector.scss',
})
export class LanguageSelector {
  private readonly languageService = inject(LanguageService);

  readonly language = this.languageService.language;
  readonly supportedLanguages = Object.entries(
    this.languageService.supportedLanguages,
  );
  readonly label = computed(() => this.languageService.t('language_label'));

  onLanguageChange(lang: string): void {
    this.languageService.setLanguage(lang);
  }
}
