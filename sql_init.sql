-- SQL Server initialization script for AI Portal usage tracking

-- Create logins table for user authentication tracking
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'logins')
BEGIN
    CREATE TABLE logins (
        id INT IDENTITY(1,1) PRIMARY KEY,
        display_name NVARCHAR(255),
        username NVARCHAR(255),
        email NVARCHAR(255),
        department NVARCHAR(255),
        login_time DATETIME,
        reporting_period NVARCHAR(6),  -- YYYYMM format
        client_ip NVARCHAR(50),
        user_agent NVARCHAR(500),
        session_id NVARCHAR(255)
    );
    
    -- Add index for efficient querying
    CREATE INDEX idx_logins_email ON logins(email);
    CREATE INDEX idx_logins_reporting_period ON logins(reporting_period);
    CREATE INDEX idx_logins_login_time ON logins(login_time);
    CREATE INDEX idx_logins_session_id ON logins(session_id);
END

-- Create usage table for app interaction tracking
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'usage')
BEGIN
    CREATE TABLE usage (
        id INT IDENTITY(1,1) PRIMARY KEY,
        display_name NVARCHAR(255),
        username NVARCHAR(255),
        email NVARCHAR(255),
        app_name NVARCHAR(255),
        app_category NVARCHAR(255),
        app_action NVARCHAR(MAX),
        usage_time DATETIME,
        reporting_period NVARCHAR(6),  -- YYYYMM format
        session_id NVARCHAR(255)
    );
    
    -- Add indexes for efficient querying
    CREATE INDEX idx_usage_email ON usage(email);
    CREATE INDEX idx_usage_app_name ON usage(app_name);
    CREATE INDEX idx_usage_app_category ON usage(app_category);
    CREATE INDEX idx_usage_reporting_period ON usage(reporting_period);
    CREATE INDEX idx_usage_usage_time ON usage(usage_time);
    CREATE INDEX idx_usage_session_id ON usage(session_id);
END

-- Create view for user statistics
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_user_stats')
BEGIN
    EXEC('CREATE VIEW vw_user_stats AS
    SELECT 
        email,
        display_name,
        MAX(department) AS department,
        COUNT(DISTINCT CONVERT(DATE, login_time)) AS login_days,
        COUNT(DISTINCT session_id) AS session_count,
        MIN(login_time) AS first_login,
        MAX(login_time) AS last_login,
        reporting_period
    FROM 
        logins
    GROUP BY 
        email, display_name, reporting_period;');
END

-- Create view for app usage statistics
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_app_usage')
BEGIN
    EXEC('CREATE VIEW vw_app_usage AS
    SELECT 
        app_name,
        app_category,
        COUNT(*) AS usage_count,
        COUNT(DISTINCT email) AS unique_users,
        reporting_period
    FROM 
        usage
    GROUP BY 
        app_name, app_category, reporting_period;');
END

-- Create view for user-app interaction
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_user_app_interactions')
BEGIN
    EXEC('CREATE VIEW vw_user_app_interactions AS
    SELECT 
        u.email,
        u.display_name,
        u.app_name,
        u.app_category,
        COUNT(*) AS interaction_count,
        MIN(u.usage_time) AS first_interaction,
        MAX(u.usage_time) AS last_interaction,
        u.reporting_period
    FROM 
        usage u
    GROUP BY 
        u.email, u.display_name, u.app_name, u.app_category, u.reporting_period;');
END

-- Create stored procedure for getting monthly user activity report
IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_monthly_user_activity')
BEGIN
    EXEC('CREATE PROCEDURE sp_monthly_user_activity
        @reporting_period NVARCHAR(6) = NULL
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- If no reporting period is provided, use the current month
        IF @reporting_period IS NULL
            SET @reporting_period = FORMAT(GETDATE(), ''yyyyMM'');
            
        -- Get user activity for the specified month
        SELECT
            l.email,
            l.display_name,
            l.department,
            COUNT(DISTINCT CONVERT(DATE, l.login_time)) AS login_days,
            (SELECT COUNT(*) FROM usage u WHERE u.email = l.email AND u.reporting_period = @reporting_period) AS total_app_interactions,
            (SELECT COUNT(DISTINCT app_name) FROM usage u WHERE u.email = l.email AND u.reporting_period = @reporting_period) AS unique_apps_used,
            (SELECT TOP 1 app_name FROM usage u WHERE u.email = l.email AND u.reporting_period = @reporting_period 
             GROUP BY app_name ORDER BY COUNT(*) DESC) AS most_used_app
        FROM
            logins l
        WHERE
            l.reporting_period = @reporting_period
        GROUP BY
            l.email, l.display_name, l.department
        ORDER BY
            login_days DESC, total_app_interactions DESC;
    END');
END

-- Create stored procedure for getting app usage report
IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_app_usage_report')
BEGIN
    EXEC('CREATE PROCEDURE sp_app_usage_report
        @reporting_period NVARCHAR(6) = NULL
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- If no reporting period is provided, use the current month
        IF @reporting_period IS NULL
            SET @reporting_period = FORMAT(GETDATE(), ''yyyyMM'');
            
        -- Get app usage for the specified month
        SELECT
            app_name,
            app_category,
            COUNT(*) AS total_interactions,
            COUNT(DISTINCT email) AS unique_users,
            COUNT(*) / CAST(COUNT(DISTINCT email) AS FLOAT) AS avg_interactions_per_user,
            MIN(usage_time) AS first_usage,
            MAX(usage_time) AS last_usage
        FROM
            usage
        WHERE
            reporting_period = @reporting_period
        GROUP BY
            app_name, app_category
        ORDER BY
            total_interactions DESC;
    END');
END

-- Create stored procedure for getting user journey analysis
IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_user_journey_analysis')
BEGIN
    EXEC('CREATE PROCEDURE sp_user_journey_analysis
        @email NVARCHAR(255)
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- Get user basic info
        SELECT TOP 1
            display_name,
            email,
            department,
            MIN(login_time) OVER() AS first_login,
            MAX(login_time) OVER() AS last_login,
            COUNT(*) OVER() AS total_logins
        FROM
            logins
        WHERE
            email = @email;
            
        -- Get app usage journey
        SELECT
            app_name,
            app_category,
            COUNT(*) AS usage_count,
            MIN(usage_time) AS first_usage,
            MAX(usage_time) AS last_usage,
            DATEDIFF(DAY, MIN(usage_time), MAX(usage_time)) AS usage_span_days
        FROM
            usage
        WHERE
            email = @email
        GROUP BY
            app_name, app_category
        ORDER BY
            first_usage;
            
        -- Get daily app usage pattern
        SELECT
            CONVERT(DATE, usage_time) AS usage_date,
            COUNT(*) AS interaction_count,
            COUNT(DISTINCT app_name) AS unique_apps_used,
            STRING_AGG(DISTINCT app_name, '', '') AS apps_used
        FROM
            usage
        WHERE
            email = @email
        GROUP BY
            CONVERT(DATE, usage_time)
        ORDER BY
            usage_date;
    END');
END

PRINT 'Database initialization completed successfully!';
