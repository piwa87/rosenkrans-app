import { HttpClient } from '@angular/common/http';
import { Injectable, signal, computed } from '@angular/core';
import {
  Translations,
  UI_TRANSLATIONS,
  SUPPORTED_LANGUAGES,
} from '../models/rosary-state.model';
import { catchError, EMPTY } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class LanguageService {
  readonly supportedLanguages = SUPPORTED_LANGUAGES;

  private readonly _language = signal<string>('en');
  readonly language = this._language.asReadonly();

  readonly translations = computed<Translations>(
    () => UI_TRANSLATIONS[this._language()] ?? UI_TRANSLATIONS['en'],
  );

  constructor(private http: HttpClient) {}

  /** Interpolate {key} placeholders in a translation string. */
  t(key: string, values?: Record<string, string | number>): string {
    const pack = this.translations();
    let text = pack[key] ?? key;
    if (values) {
      for (const [k, v] of Object.entries(values)) {
        text = text.replace(`{${k}}`, String(v));
      }
    }
    return text;
  }

  /** Switch to a new language via the Flask `/language` endpoint. */
  setLanguage(lang: string): void {
    this.http
      .post<{ language: string }>('/language', { language: lang })
      .pipe(
        catchError((err) => {
          console.error('Could not switch language', err);
          return EMPTY;
        }),
      )
      .subscribe((res) => {
        this._language.set(res.language);
      });
  }

  /** Seed the current language (called once on app start). */
  initLanguage(lang: string): void {
    this._language.set(lang);
  }
}
