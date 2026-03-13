import requests
from bs4 import BeautifulSoup
import json

def get_linkedin_jobs(job_title=None, location=None, remote_only=False):
    """
    Args:
        job_title (str): e.g., 'Software Engineering'
        location (str): e.g., 'Delhi'
        remote_only (bool): If True, filters for Remote only (f_WT=2)
    """
    
    # Base Guest API URL
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    # Build dynamic parameters
    # f_TPR=r86400 filters for the last 24 hours (Latest)
    params = {
        "keywords": job_title if job_title else "",
        "location": location if location else "",
        "f_TPR": "r86400", 
        "start": 0,
        "refresh": "true",
        "sortBy": "DD" # Force Date Descending sort
    }

    # Add Remote Filter if requested
    if remote_only:
        params["f_WT"] = "2"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    print(f"Scraping Latest Jobs | Title: {params['keywords']} | Loc: {params['location']} | Remote: {remote_only}")

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"LinkedIn rejected request (Status {response.status_code})"}

        soup = BeautifulSoup(response.text, "lxml")
        jobs = []

        # Find all job card list items
        for li in soup.find_all("li"):
            # Title & URL
            title_el = li.find("a", href=lambda x: x and "/jobs/view/" in x)
            if title_el:
                job_name = title_el.get_text(strip=True)
                job_url = title_el.get("href", "").split("?")[0]
                
                # Company Name
                company_el = li.select_one(".base-search-card__subtitle") or li.find("a", href=lambda x: x and "/company/" in x)
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                
                # Location
                loc_el = li.select_one(".job-search-card__location")
                loc_text = loc_el.get_text(strip=True) if loc_el else "N/A"
                
                # Freshness Label (e.g., "2 hours ago")
                time_el = li.find("time")
                posted_time = time_el.get_text(strip=True) if time_el else "Recently"

                jobs.append({
                    "title": job_name,
                    "company": company,
                    "location": loc_text,
                    "posted": posted_time,
                    "url": job_url
                })

        return {"jobs": jobs, "total_found": len(jobs)}

    except Exception as e:
        return {"error": str(e)}

# --- TESTING INDEPENDENT FILTERS ---
if __name__ == "__main__":
    
    # Example 1: Independent Location (All jobs in Delhi, Latest)
    print("\n[TEST 1] All latest jobs in Delhi:")
    res1 = get_linkedin_jobs(job_title=None, location="Delhi")
    print(json.dumps(res1, indent=2))

    # Example 2: Independent Job Type (Software Engineering anywhere, Latest)
    print("\n[TEST 2] Latest Software Engineering jobs globally:")
    res2 = get_linkedin_jobs(job_title="Software Engineering", location=None)
    print(json.dumps(res2, indent=2))

    # Example 3: Remote Only + Job Title (Latest)
    print("\n[TEST 3] Latest Remote AI Engineer jobs:")
    res3 = get_linkedin_jobs(job_title="AI Engineer", location=None, remote_only=True)
    print(json.dumps(res3, indent=2))