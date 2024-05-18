import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { DropdownModule } from 'primeng/dropdown';

import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-prediction',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    ButtonModule,
    DropdownModule,
    ChartModule,
  ],
  templateUrl: './prediction.component.html',
  styleUrls: ['./prediction.component.scss'],
})
export class PredictionComponent implements OnInit {
  stocks: any[] = [];
  selectedStock: string = '';
  totalStocks: number = 0;
  predictionData: any;
  predictionOptions: any;
  chartData: any;
  predictedPrices: number[] = [];
  chartOptions: any;
  private baseUrl = 'http://127.0.0.1:5000';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchAvailableStocks();
  }

  fetchAvailableStocks(): void {
    this.http.get<any[]>(`${this.baseUrl}/stocks`).subscribe(
      (stocks) => {
        this.stocks = stocks.map((stock) => ({
          name: stock.code,
          code: stock.code,
        }));
        this.fetchStockNames();
      },
      (error) => {
        console.error('Error fetching available stocks:', error);
      }
    );
  }

  fetchStockNames(): void {
    this.stocks.forEach((stock, index) => {
      this.http.get<any>(`${this.baseUrl}/stock/${stock.code}`).subscribe(
        (stockInfo) => {
          this.stocks[index].name = stockInfo.name;
        },
        (error) => {
          console.error(`Error fetching stock name for ${stock.code}:`, error);
        }
      );
    });
  }

  onStockSelected(): void {
    this.trainModel();
    this.http.get(`${this.baseUrl}/stocks/${this.selectedStock}`).subscribe(
      (data) => {
        this.updateChart(data);
      },
      (error) => {
        console.error('Error fetching stock data:', error);
      }
    );
  }

  updateChart(stockData: any): void {
    this.chartData = {
      labels: stockData.labels,
      datasets: [
        {
          label: this.selectedStock,
          data: stockData.prices,
          borderColor: 'blue',
          fill: false,
        },
      ],
    };

    this.chartOptions = {
      responsive: true,
    };
  }

  trainModel(): void {
    this.http.post(`${this.baseUrl}/train/${this.selectedStock}`, {}).subscribe(
      (response) => {
        console.log('Model trained successfully for', this.selectedStock);
      },
      (error) => {
        console.error('Error training the model:', error);
      }
    );
  }

  predictPrice(): void {
    this.http
      .get<any>(`${this.baseUrl}/predict/${this.selectedStock}`)
      .subscribe(
        (response) => {
          this.predictedPrices = response.prices;
          this.updatePredictionChart();
        },
        (error) => {
          console.error('Error predicting prices:', error);
        }
      );
  }

  updatePredictionChart(): void {
    this.predictionData = {
      labels: Array.from(
        { length: this.predictedPrices.length },
        (_, i) => i + 1
      ),
      datasets: [
        {
          label: 'Predicted Prices',
          data: this.predictedPrices,
          borderColor: 'red',
          fill: false,
        },
      ],
    };

    this.predictionOptions = {
      responsive: true,
    };
  }
}
