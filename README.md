# Athlete Nutrition Tracker 🍏⚽

A Streamlit application for athletes to track their nutrition intake and weight measurements, with data stored in MongoDB.

![App Screenshot](screenshots/app_preview.png) *(Optional: Add actual screenshot later)*

## Features ✨

- **Food Diary**: Record daily meals with:
  - Multiple food items per meal
  - Custom portion sizes and units
  - Meal type classification (Breakfast/Lunch/Dinner/Snack)
  - Activity context (Match/Training/Rest)

- **Weight Tracking**: Log weight measurements:
  - Before/after activities
  - With activity type context
  - Historical data tracking

- **Player Management**:
  - Multi-player support
  - Persistent player selection

## Prerequisites 📋

- Python 3.8+
- MongoDB Atlas account or local MongoDB instance
- Streamlit

## Installation 🛠️

1. Clone the repository
```bash
git clone https://github.com/yourusername/athlete-nutrition-tracker.git
cd athlete-nutrition-tracker
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

## Configuration ⚙️

1. Create .streamlit/secrets.toml file with MongoDB credentials:
```bash
[MongoDB]
mongo_username = "your_username"
mongo_password = "your_password"
mongo_cluster_url = "cluster0.abc123.mongodb.net"
database_name = "athlete_tracking"
```
2. Set up MongoDB collections:
```bash
roster (for player IDs)
meal_diary_entries
weight_registration
```

## Usage 🚀

1. Run the application:
```bash
streamlit run app.py
```
2. Access the app in your browser at http://localhost:8501

3. Application tabs:

    - Food Diary: Record daily meals
    - Weight Tracking: Log weight measurements
    - Information: Usage guidelines

## Logging 📝

- Application logs are stored in:
  
  - Console output during development
  - Rotating log files in logs/ directory:
    - app.log (current)
    - app.log.1, app.log.2 (rotated backups)
- To monitor logs in real-time:
```bash
tail -f logs/app.log
```

## Deployment 🌐

Option 1: Streamlit Sharing
- Push code to GitHub repository
- Import into Streamlit Sharing
- Set secrets in advanced settings

Option 2: Docker
- Build image:
```bash
docker build -t nutrition-tracker .
```  
- Run container:
```bash
docker run -p 8501:8501 nutrition-tracker
```

## Database Schema 🗃️

- Meal Diary Entries
```bash
{
  player_id: String,
  meal_date: Number,  // YYYYMMDD format
  day_type: String,  // "Match", "Training", "Rest"
  meal_type: String, // "Breakfast", "Lunch", etc.
  meal_elements: [
    {
      time: String,   // "HH:MM"
      food_product: String,
      amount_value: Number,
      amount_unit: String
    }
  ]
}
```
- Weight Registrations
```bash
{
  player_id: String,
  registration_date: Number, // YYYYMMDD format
  day_type: String,         // "Wedstrijd", "Training"
  weight_before: Number,    // kg
  weight_after: Number      // kg
}
```
## Troubleshooting 🐛

Common issues:
- Connection errors: Verify MongoDB credentials in secrets.toml
- Missing player IDs: Ensure roster collection is populated
- Form submission failures: Check application logs for details

## Contributing 🤝

- Fork the project
- Create your feature branch (git checkout -b feature/AmazingFeature)
- Commit your changes (git commit -m 'Add some amazing feature')
- Push to the branch (git push origin feature/AmazingFeature)
- Open a Pull Request

## License 📄

Distributed under the MIT License. See LICENSE for more information.


