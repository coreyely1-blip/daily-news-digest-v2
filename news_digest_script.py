#!/usr/bin/env python3
"""
Daily News Digest Generator
Fetches news articles and sports scores from various sources and sends an email digest.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class NewsDigestGenerator:
    def __init__(self):
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.sports_api_key = os.environ.get('SPORTS_API_KEY', '')
        self.sender_email = os.environ.get('SENDER_EMAIL')
        self.sender_password = os.environ.get('SENDER_PASSWORD')
        self.recipient_email = os.environ.get('RECIPIENT_EMAIL')
        
        if not all([self.news_api_key, self.sender_email, self.sender_password, self.recipient_email]):
            raise ValueError("Missing required environment variables")
    
    def fetch_news(self, query: str, num_articles: int = 5) -> List[Dict[str, Any]]:
        """Fetch news articles from NewsAPI"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'sortBy': 'popularity',
                'language': 'en',
                'pageSize': num_articles,
                'apiKey': self.news_api_key
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', [])[:num_articles]:
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'image': article.get('urlToImage', ''),
                    'publishedAt': article.get('publishedAt', '')
                })
            return articles
        except Exception as e:
            print(f"Error fetching news for '{query}': {e}")
            return []
    
    def fetch_nba_scores(self) -> Dict[str, Any]:
        """Fetch NBA scores from ESPN"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for event in data.get('events', []):
                competitors = event.get('competitions', [{}])[0].get('competitors', [])
                if len(competitors) >= 2:
                    games.append({
                        'home': competitors[0].get('team', {}).get('displayName', ''),
                        'away': competitors[1].get('team', {}).get('displayName', ''),
                        'home_score': competitors[0].get('score', '-'),
                        'away_score': competitors[1].get('score', '-'),
                        'status': event.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('description', 'TBD')
                    })
            return {'games': games, 'date': datetime.now().strftime('%Y-%m-%d')}
        except Exception as e:
            print(f"Error fetching NBA scores: {e}")
            return {'games': [], 'date': datetime.now().strftime('%Y-%m-%d')}
    
    def fetch_nfl_scores(self) -> Dict[str, Any]:
        """Fetch NFL scores from ESPN"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for event in data.get('events', []):
                competitors = event.get('competitions', [{}])[0].get('competitors', [])
                if len(competitors) >= 2:
                    games.append({
                        'home': competitors[0].get('team', {}).get('displayName', ''),
                        'away': competitors[1].get('team', {}).get('displayName', ''),
                        'home_score': competitors[0].get('score', '-'),
                        'away_score': competitors[1].get('score', '-'),
                        'status': event.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('description', 'TBD')
                    })
            return {'games': games}
        except Exception as e:
            print(f"Error fetching NFL scores: {e}")
            return {'games': []}
    
    def fetch_soccer_scores(self, league: str) -> List[Dict[str, Any]]:
        """Fetch soccer scores - uses ESPN endpoint"""
        try:
            league_map = {
                'premier-league': 'soccer/eng.1',
                'champions-league': 'soccer/uefa.champions',
                'europa-league': 'soccer/uefa.europa',
                'championship': 'soccer/eng.2',
                'fa-cup': 'soccer/eng.fa',
                'carabao-cup': 'soccer/eng.cup'
            }
            
            league_id = league_map.get(league, '')
            if not league_id:
                return []
            
            url = f"https://site.api.espn.com/apis/site/v2/sports/{league_id}/scoreboard"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for event in data.get('events', [])[:5]:  # Top 5 games
                competitors = event.get('competitions', [{}])[0].get('competitors', [])
                if len(competitors) >= 2:
                    games.append({
                        'home': competitors[0].get('team', {}).get('displayName', ''),
                        'away': competitors[1].get('team', {}).get('displayName', ''),
                        'home_score': competitors[0].get('score', '-'),
                        'away_score': competitors[1].get('score', '-'),
                        'status': event.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('description', 'TBD')
                    })
            return games
        except Exception as e:
            print(f"Error fetching {league} scores: {e}")
            return []
    
    def generate_html_digest(self) -> str:
        """Generate the HTML email digest"""
        html = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                    .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; }
                    h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
                    h2 { color: #007bff; margin-top: 30px; border-left: 4px solid #007bff; padding-left: 10px; }
                    .article { margin: 15px 0; padding: 15px; border-left: 4px solid #ddd; }
                    .article-title { font-weight: bold; color: #333; }
                    .article-summary { color: #666; font-size: 14px; margin: 5px 0; }
                    .article-source { color: #999; font-size: 12px; }
                    .article-link { color: #007bff; text-decoration: none; font-size: 12px; }
                    .score-item { padding: 10px; margin: 5px 0; background: #f9f9f9; border-radius: 4px; }
                    .score-teams { font-weight: bold; }
                    .score-final { color: #007bff; font-weight: bold; }
                    .footer { text-align: center; color: #999; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📰 Daily News Digest - {}</h1>
        """.format(datetime.now().strftime('%A, %B %d, %Y'))
        
        # Fetch all news sections
        news_sections = {
            'Top 5 US News': ('US news', 5),
            'Top 5 Europe News': ('Europe news', 5),
            'Top 5 Africa News': ('Africa news', 5),
            'Top 3 India News': ('India news', 3),
            'Top 3 China News': ('China news', 3),
            'Top 5 NBA News': ('NBA basketball', 5),
            'Top 5 NFL News': ('NFL football', 5),
            'Top 5 Premier League News': ('English Premier League', 5),
            'Top 2 West Ham News': ('West Ham United', 2),
        }
        
        for section_title, (query, count) in news_sections.items():
            articles = self.fetch_news(query, count)
            html += f"<h2>{section_title}</h2>\n"
            
            if articles:
                for article in articles:
                    html += f"""
                    <div class="article">
                        <div class="article-title">{article['title']}</div>
                        <div class="article-summary">{article['description'][:200]}...</div>
                        <div class="article-source">{article['source']}</div>
                        <a href="{article['url']}" class="article-link">Read full article →</a>
                    </div>
                    """
            else:
                html += "<p style='color: #999;'>No articles found at this time.</p>\n"
        
        # NBA Scores
        html += "<h2>🏀 NBA Scores (Previous Day)</h2>\n"
        nba_data = self.fetch_nba_scores()
        if nba_data['games']:
            for game in nba_data['games']:
                html += f"""
                <div class="score-item">
                    <div class="score-teams">{game['away']} @ {game['home']}</div>
                    <div class="score-final">{game['away_score']} - {game['home_score']}</div>
                    <div class="score-source">{game['status']}</div>
                </div>
                """
        else:
            html += "<p style='color: #999;'>No games to display.</p>\n"
        
        # Soccer Scores
        html += "<h2>⚽ Soccer Scores</h2>\n"
        soccer_leagues = {
            'Premier League': 'premier-league',
            'Champions League': 'champions-league',
            'Europa League': 'europa-league',
            'EFL Championship': 'championship',
            'FA Cup': 'fa-cup',
            'Carabao Cup': 'carabao-cup'
        }
        
        for league_name, league_id in soccer_leagues.items():
            games = self.fetch_soccer_scores(league_id)
            html += f"<h3>{league_name}</h3>\n"
            if games:
                for game in games:
                    html += f"""
                    <div class="score-item">
                        <div class="score-teams">{game['away']} vs {game['home']}</div>
                        <div class="score-final">{game['away_score']} - {game['home_score']}</div>
                    </div>
                    """
            else:
                html += "<p style='color: #999;'>No matches to display.</p>\n"
        
        html += """
                    <div class="footer">
                        <p>This is an automated daily digest. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return html
    
    def send_email(self, html_content: str):
        """Send the digest via email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📰 Daily News Digest - {datetime.now().strftime('%A, %B %d, %Y')}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {self.recipient_email}")
        except Exception as e:
            print(f"Error sending email: {e}")
            raise

def main():
    try:
        generator = NewsDigestGenerator()
        print("Generating daily news digest...")
        html_digest = generator.generate_html_digest()
        print("Sending email...")
        generator.send_email(html_digest)
        print("Daily digest completed successfully!")
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
