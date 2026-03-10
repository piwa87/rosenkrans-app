import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { RosaryVisualizer, BEADS } from './rosary-visualizer';

describe('RosaryVisualizer', () => {
  let component: RosaryVisualizer;
  let fixture: ComponentFixture<RosaryVisualizer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RosaryVisualizer],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(RosaryVisualizer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have 55 beads', () => {
    expect(BEADS.length).toBe(55);
  });

  it('should mark every 11th bead as Our Father', () => {
    const ourFatherBeads = BEADS.filter((b) => b.isOurFather);
    expect(ourFatherBeads.length).toBe(5);
    ourFatherBeads.forEach((b, i) => {
      expect(b.decadeNumber).toBe(i + 1);
    });
  });

  it('should render an SVG element', () => {
    fixture.detectChanges();
    const svg = fixture.nativeElement.querySelector('svg');
    expect(svg).toBeTruthy();
  });
});
