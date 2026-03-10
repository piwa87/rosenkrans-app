import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { StatusPanel } from './status-panel';

describe('StatusPanel', () => {
  let component: StatusPanel;
  let fixture: ComponentFixture<StatusPanel>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatusPanel],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(StatusPanel);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show 5 decade indicators', () => {
    fixture.detectChanges();
    const dots = fixture.nativeElement.querySelectorAll('.decade-dot');
    expect(dots.length).toBe(5);
  });

  it('should show waiting text when no state', () => {
    fixture.detectChanges();
    expect(component.statusText()).toContain('Waiting');
  });
});
