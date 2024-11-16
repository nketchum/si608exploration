import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re

class CongressVoteScraper:
    def __init__(self):
        self.base_url = "https://www.congress.gov"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        self.session = requests.Session()
    
    def get_member_votes(self, congress: int, bill_number: str) -> pd.DataFrame:
        """
        Get all member votes for a specific bill using XML/RSS feed.
        
        Args:
            congress: Congress number (e.g., 118)
            bill_number: Bill number (e.g., "hr3")
        """
        # Clean bill number format
        bill_number = bill_number.lower().strip()
        if bill_number.startswith('h'):
            chamber = 'house'
        elif bill_number.startswith('s'):
            chamber = 'senate'
        else:
            raise ValueError("Bill number must start with 'h' or 's'")
        
        try:
            # First get the roll call numbers from the RSS feed
            rss_url = f"https://www.congress.gov/bill/{congress}th-congress/{bill_number}/all-actions/rss.xml"
            response = self.session.get(rss_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'xml')
            
            # Find vote links in the RSS feed
            vote_numbers = []
            for item in soup.find_all('item'):
                description = item.description.text
                if 'Roll Call Vote' in description:
                    # Extract roll call number using regex
                    match = re.search(r'Roll Call Vote (\d+)', description)
                    if match:
                        vote_numbers.append(match.group(1))
            
            if not vote_numbers:
                print(f"No votes found for {bill_number.upper()} in the {congress}th Congress")
                return pd.DataFrame()
            
            # Get votes for each roll call number
            all_votes = []
            for vote_num in vote_numbers:
                try:
                    # Use the XML feed for vote results
                    vote_url = f"https://www.congress.gov/roll-call-vote/{congress}th-congress/{chamber}/vote-{vote_num}.xml"
                    votes = self._scrape_vote_xml(vote_url)
                    all_votes.extend(votes)
                    time.sleep(1)
                except Exception as e:
                    print(f"Error scraping vote number {vote_num}: {str(e)}")
            
            # Convert to DataFrame
            df = pd.DataFrame(all_votes)
            
            # Clean up vote values
            if not df.empty:
                df['vote'] = df['vote'].replace({
                    'Yea': 'Yes',
                    'Aye': 'Yes',
                    'Nay': 'No'
                })
            
            return df
            
        except Exception as e:
            print(f"Error fetching votes: {str(e)}")
            return pd.DataFrame()
    
    def _scrape_vote_xml(self, url: str) -> list:
        """Scrape vote data from XML feed."""
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'xml')
        
        # Get vote metadata
        try:
            vote_date = soup.find('vote-date').text
            chamber = soup.find('chamber').text
        except:
            vote_date = None
            chamber = None
        
        votes = []
        
        # Process each member's vote
        for member in soup.find_all('member'):
            try:
                name = member.find('legislator').text
                party = member.find('party').text
                state = member.find('state').text
                vote = member.find('vote').text
                
                votes.append({
                    'name': name,
                    'party': party,
                    'state': state,
                    'vote': vote,
                    'chamber': chamber,
                    'vote_date': vote_date
                })
            except Exception as e:
                print(f"Error processing member vote: {str(e)}")
        
        return votes

def print_vote_summary(df: pd.DataFrame):
    """Print a summary of the vote results."""
    if df.empty:
        return
    
    print("\nVote Summary:")
    print("-------------")
    
    # Overall totals
    print("\nOverall Vote Totals:")
    print(df['vote'].value_counts())
    
    # By party
    print("\nVotes by Party:")
    print(pd.crosstab(df['party'], df['vote']))
    
    # Result calculation
    yes_votes = df['vote'].str.contains('Yes', case=False).sum()
    total_votes = len(df[df['vote'].str.contains('Yes|No', case=False)])
    if total_votes > 0:
        print(f"\nFinal Result: {'PASSED' if yes_votes > total_votes/2 else 'FAILED'}")
        print(f"Yes Votes: {yes_votes} ({yes_votes/total_votes*100:.1f}%)")

def main():
    scraper = CongressVoteScraper()
    
    # Example usage
    congress = 118  # Current congress
    bill = "hr3"    # Example bill
    
    print(f"Fetching votes for {bill.upper()} from the {congress}th Congress...")
    
    df = scraper.get_member_votes(congress, bill)
    
    if not df.empty:
        # Print summary
        print_vote_summary(df)
        
        # Save to CSV
        output_file = f"votes_{congress}_{bill}_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(output_file, index=False)
        print(f"\nDetailed results saved to {output_file}")
    else:
        print("No votes found or error occurred.")

if __name__ == "__main__":
    main()
    scraper = CongressVoteScraper()
    df = scraper.get_member_votes(118, "hr3")

    # Print summary
    print_vote_summary(df)

    # Access raw data
    print(df.head())
