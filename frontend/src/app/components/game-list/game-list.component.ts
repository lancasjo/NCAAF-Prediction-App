import { Component, OnInit } from '@angular/core';
import { GameService } from '../../game.service';
import { Game } from './game.model'; // Import the Game type from the separate file


@Component({
  selector: 'app-game-list',
  templateUrl: './game-list.component.html',
  styleUrls: ['./game-list.component.css']
})
export class GameListComponent implements OnInit {
  weeks: any[] = [];

  constructor(private gameService: GameService) { }

  ngOnInit(): void {
    this.gameService.getGames().subscribe(data => {
      console.log(data);
      this.weeks = data;
      this.weeks.forEach(week => {
        week.Games = week.Games.filter((game: Game) => {
          game.Prediction = Math.round(game.Prediction)
          return this.difference(game.Prediction, game.Spread) > 4
        })
      });
    });
  }
  difference(prediction: number, spread: number): number {
    return Math.abs(prediction - spread);
  }
  generateGoogleSearchLink(game: any): string {
    const searchQuery = `${game.Away} vs ${game.Home} game`;
    const encodedQuery = encodeURIComponent(searchQuery);
    return `https://www.google.com/search?q=${encodedQuery}`;
  }
}