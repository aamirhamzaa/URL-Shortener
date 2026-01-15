import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import Counter
import io
import base64
import config
from logger import logger
from database import Database

class Analytics:
    """Analytics engine for generating insights"""
    
    def __init__(self, database: Database):
        """
        Initialize analytics
        
        Args:
            database: Database instance
        """
        self.db = database
        logger.info("Analytics engine initialized")
    
    def get_clicks_over_time(self, short_code=None, days=30):
        """
        Get clicks over time
        
        Args:
            short_code: Specific short code (None for all)
            days: Number of days to analyze
        
        Returns:
            Dictionary with dates and click counts
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        clicks = self.db.get_clicks(
            short_code=short_code,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Group by date
        date_counts = Counter()
        for click in clicks:
            try:
                date = datetime.fromisoformat(click['clicked_at']).date()
                date_counts[date] += 1
            except Exception as e:
                logger.error(f"Error parsing click date: {e}")
                continue
        
        # Fill missing dates with 0
        current_date = start_date.date()
        while current_date <= end_date.date():
            if current_date not in date_counts:
                date_counts[current_date] = 0
            current_date += timedelta(days=1)
        
        # Sort by date
        sorted_data = sorted(date_counts.items())
        
        return {
            'dates': [str(date) for date, _ in sorted_data],
            'counts': [count for _, count in sorted_data]
        }
    
    def get_top_urls(self, limit=10):
        """
        Get top URLs by click count
        
        Args:
            limit: Number of results
        
        Returns:
            List of URLs with click counts
        """
        urls = self.db.get_all_urls()
        
        # Add click counts and sort
        for url in urls:
            url['click_count'] = self.db.get_click_count(url['short_code'])
        
        sorted_urls = sorted(urls, key=lambda x: x['click_count'], reverse=True)
        return sorted_urls[:limit]
    
    def get_geographic_distribution(self, short_code=None):
        """
        Get geographic distribution of clicks
        
        Args:
            short_code: Specific short code (None for all)
        
        Returns:
            Dictionary with country counts
        """
        clicks = self.db.get_clicks(short_code=short_code)
        
        country_counts = Counter()
        for click in clicks:
            # FIXED: Handle empty/None strings properly
            country = str(click.get('country', '')).strip() if click.get('country') else ''
            if country and country != 'None' and country != '':
                country_counts[country] += 1
        
        if not country_counts:
            return {'Unknown': len(clicks)} if clicks else {}
        
        return dict(country_counts.most_common(10))
    
    def get_browser_distribution(self, short_code=None):
        """
        Get browser distribution
        
        Args:
            short_code: Specific short code (None for all)
        
        Returns:
            Dictionary with browser counts
        """
        clicks = self.db.get_clicks(short_code=short_code)
        
        browser_counts = Counter()
        for click in clicks:
            # FIXED: Handle empty/None strings properly
            browser = str(click.get('browser', '')).strip() if click.get('browser') else ''
            if browser and browser != 'None' and browser != '':
                browser_counts[browser] += 1
            else:
                browser_counts['Unknown'] += 1
        
        return dict(browser_counts.most_common(10))
    
    def get_device_distribution(self, short_code=None):
        """
        Get device distribution
        
        Args:
            short_code: Specific short code (None for all)
        
        Returns:
            Dictionary with device counts
        """
        clicks = self.db.get_clicks(short_code=short_code)
        
        device_counts = Counter()
        for click in clicks:
            # FIXED: Handle empty/None strings properly
            device = str(click.get('device', '')).strip() if click.get('device') else ''
            if device and device != 'None' and device != '':
                device_counts[device] += 1
            else:
                device_counts['Unknown'] += 1
        
        return dict(device_counts.most_common())
    
    def get_hourly_distribution(self, short_code=None):
        """
        Get clicks by hour of day
        
        Args:
            short_code: Specific short code (None for all)
        
        Returns:
            Dictionary with hourly counts
        """
        clicks = self.db.get_clicks(short_code=short_code)
        
        hour_counts = Counter()
        for click in clicks:
            try:
                hour = datetime.fromisoformat(click['clicked_at']).hour
                hour_counts[hour] += 1
            except Exception as e:
                logger.error(f"Error parsing click hour: {e}")
                continue
        
        # Fill missing hours
        for hour in range(24):
            if hour not in hour_counts:
                hour_counts[hour] = 0
        
        return dict(sorted(hour_counts.items()))
    
    def generate_clicks_chart(self, short_code=None, days=30):
        """
        Generate clicks over time chart
        
        Args:
            short_code: Specific short code (None for all)
            days: Number of days
        
        Returns:
            Base64 encoded image or None
        """
        try:
            data = self.get_clicks_over_time(short_code, days)
            
            if not data['dates'] or not data['counts']:
                logger.warning("No click data available for chart")
                return None
            
            plt.figure(figsize=(10, 6) , dpi = 150)
            plt.plot(data['dates'], data['counts'], marker='o', linewidth=2, markersize=4, color='#4CAF50')
            plt.xlabel('Date')
            plt.ylabel('Clicks')
            plt.title(f'Clicks Over Time ({days} days)')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            logger.debug("Clicks chart generated successfully")
            return image_base64
        except Exception as e:
            logger.error(f"Error generating clicks chart: {e}")
            plt.close()
            return None
    
    def generate_geographic_chart(self, short_code=None):
        """
        Generate geographic distribution chart
        
        Args:
            short_code: Specific short code (None for all)
        
        Returns:
            Base64 encoded image or None
        """
        try:
            data = self.get_geographic_distribution(short_code)
            
            if not data:
                logger.warning("No geographic data available for chart")
                return None
            
            plt.figure(figsize=(10, 6))
            countries = list(data.keys())
            counts = list(data.values())
            
            plt.barh(countries, counts, color='#4CAF50')
            plt.xlabel('Clicks')
            plt.ylabel('Country')
            plt.title('Geographic Distribution')
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            logger.debug("Geographic chart generated successfully")
            return image_base64
        except Exception as e:
            logger.error(f"Error generating geographic chart: {e}")
            plt.close()
            return None
    
    def generate_pie_chart(self, data_dict, title):
        """
        Generate pie chart
        
        Args:
            data_dict: Data dictionary
            title: Chart title
        
        Returns:
            Base64 encoded image or None
        """
        try:
            if not data_dict:
                logger.warning(f"No data available for pie chart: {title}")
                return None
            
            # Filter out zero values
            data_dict = {k: v for k, v in data_dict.items() if v > 0}
            
            if not data_dict:
                return None
            
            plt.figure(figsize=(8, 8))
            labels = list(data_dict.keys())
            sizes = list(data_dict.values())
            
            colors = ['#4CAF50', '#2196F3', '#FFC107', '#FF5722', '#9C27B0', '#00BCD4', '#CDDC39']
            
            # Ensure we have enough colors
            while len(colors) < len(labels):
                colors.extend(colors)
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors[:len(labels)], startangle=90)
            plt.title(title)
            plt.axis('equal')
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            logger.debug(f"Pie chart generated successfully: {title}")
            return image_base64
        except Exception as e:
            logger.error(f"Error generating pie chart ({title}): {e}")
            plt.close()
            return None
    
    def export_analytics_report(self, short_code=None, format='txt'):
        """
        Export analytics report
        
        Args:
            short_code: Specific short code (None for all)
            format: Export format (txt, csv, json)
        
        Returns:
            Report string
        """
        stats = self.db.get_statistics()
        clicks = self.db.get_clicks(short_code=short_code, limit=100)
        
        if format == 'txt':
            report = "=" * 50 + "\n"
            report += "URL SHORTENER ANALYTICS REPORT\n"
            report += "=" * 50 + "\n\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report += "STATISTICS\n"
            report += "-" * 50 + "\n"
            report += f"Total URLs: {stats.get('total_urls', 0)}\n"
            report += f"Total Clicks: {stats.get('total_clicks', 0)}\n"
            report += f"Avg Clicks/URL: {stats.get('avg_clicks_per_url', 0):.2f}\n"
            report += f"Avg Response Time: {stats.get('avg_response_time_ms', 0):.2f}ms\n\n"
            
            if stats.get('most_clicked'):
                report += f"Most Clicked: {stats['most_clicked']['short_code']} "
                report += f"({stats['most_clicked']['clicks']} clicks)\n\n"
            
            report += "TOP COUNTRIES\n"
            report += "-" * 50 + "\n"
            geo_data = self.get_geographic_distribution(short_code)
            for country, count in geo_data.items():
                report += f"{country}: {count} clicks\n"
            
            report += "\nBROWSER DISTRIBUTION\n"
            report += "-" * 50 + "\n"
            browser_data = self.get_browser_distribution(short_code)
            for browser, count in browser_data.items():
                report += f"{browser}: {count} clicks\n"
            
            return report
        
        # Add more formats as needed
        return str(stats)
