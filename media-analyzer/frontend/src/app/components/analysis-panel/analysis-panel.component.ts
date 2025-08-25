import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Analysis, DetectionResult, VisualAnalysis } from '../../models/analysis';

@Component({
  selector: 'app-analysis-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analysis-panel.component.html',
  styleUrl: './analysis-panel.component.scss'
})
export class AnalysisPanelComponent implements OnChanges {
  @Input() analyses: Analysis[] = [];
  @Input() currentDetections: DetectionResult[] = [];
  @Input() currentVisual?: VisualAnalysis;

  ngOnChanges() {
  }

  getDetectionsByType(type: string): DetectionResult[] {
    return this.currentDetections.filter(d => d.detection_type === type);
  }

  getColorStyle(colors: number[][]): string {
    if (!colors || colors.length === 0) return '';
    const [r, g, b] = colors[0];
    return `rgb(${r}, ${g}, ${b})`;
  }
}
