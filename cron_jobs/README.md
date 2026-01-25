# Cron Jobs

This directory contains cron job scripts for scheduled tasks.

## manage_meal_plans.py

Manages the lifecycle of user meal plans by inactivating expired plans and generating new ones when needed.

### What it does:
1. Fetches all active meal plans from the `user_meal_plan` table
2. **Inactivates expired meal plans**: Sets `is_active = False` for meal plans where `end_date < today`
3. **Generates new meal plans**: For meal plans where `end_date` is exactly 2 days before today, generates a new 7-day meal plan with `start_date = old_end_date + 1 day`
4. Logs all actions and provides summary statistics

### Usage:

#### Run manually:
```bash
cd /path/to/foodeasy-backend
python3 cron_jobs/manage_meal_plans.py
```

#### Set up as a cron job:

1. Open your crontab:
```bash
crontab -e
```

2. Add a line to run the job at your desired schedule. Recommended:

   - Run daily at 2 AM (recommended):
   ```cron
   0 2 * * * cd /path/to/foodeasy-backend && /usr/bin/python3 cron_jobs/manage_meal_plans.py >> /var/log/foodeasy-cron.log 2>&1
   ```

   - Run every 12 hours:
   ```cron
   0 */12 * * * cd /path/to/foodeasy-backend && /usr/bin/python3 cron_jobs/manage_meal_plans.py >> /var/log/foodeasy-cron.log 2>&1
   ```

3. Make sure to:
   - Replace `/path/to/foodeasy-backend` with the actual path to your project
   - Replace `/usr/bin/python3` with the path to your Python 3 interpreter (find it with `which python3`)
   - Ensure the `.env` file is in the project root with proper Supabase credentials

### Output:

The script prints:
- Timestamp of execution
- Number of active meal plans found
- For each inactivated meal plan: meal plan ID, user ID, and end date
- For each new meal plan generation: user ID, old end date, and new start date
- Summary statistics:
  - Total meal plans processed
  - Number of meal plans inactivated
  - Number of new meal plans generated

### Exit Codes:
- `0`: Success
- `1`: Error occurred

### Requirements:
- Python 3.x
- All dependencies from `requirements.txt` installed
- `.env` file configured with Supabase credentials
- Database access with proper permissions
- OpenAI API key configured (for meal plan generation)
