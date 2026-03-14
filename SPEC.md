# GameSync - Mowgli Spec (v7)

## 

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

## User Journeys

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

**GameSync** - Transform your home into an immersive sports arena.

GameSync is a Home Assistant Add-on that transforms smart homes into immersive sports arenas. Designed for desktop web browsers and running entirely as a self-hosted service within Home Assistant, GameSync polls live scores from the NFL, NBA, MLB, and NHL via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

### 1. First-Time Setup and Onboarding

#### 1.1. Add-on Installation

- 1.1.1. User installs GameSync from the Home Assistant Add-on Store
- 1.1.2. User starts the add-on and opens the Web UI via Home Assistant Ingress
- 1.1.3. System detects Home Assistant instance and requests authorization to access light and media_player entities
- 1.1.4. User confirms HA integration, granting service call permissions

#### 1.2. League and Team Selection

- 1.2.1. User selects which leagues to activate from supported leagues (NFL, NBA, MLB, NHL, F1, Premier League, MLS)
- 1.2.2. System displays team discovery interface with searchable lists per activated league
- 1.2.3. User selects one or more teams to follow
- 1.2.4. For each selected team, system creates a FollowedTeam record with auto-sync disabled by default
- 1.2.5. System fetches and displays upcoming schedule for followed teams

#### 1.3. Initial Effect Configuration

- 1.3.1. User selects a followed team to configure default effects
- 1.3.2. System presents event types available for that team's league (e.g., for NFL: Touchdown, Field Goal; for NBA: Three-Pointer, Free Throw, Regular Basket)
- 1.3.3. For each event type, user configures:
  * Light effect pattern (flash, strobe, pulse, or solid color)
  * Light color selection (team colors or custom hex)
  * Target Home Assistant light entities (multi-select)
  * Sound asset selection (from built-in library)
  * Target Home Assistant media_players (multi-select)
  * Toggle to fire `gamesync_score` Home Assistant event (for power user automations)
  * Note: F1 event types include Race Win, Podium Finish, Fastest Lap, Overtake, Pit Stop, and Safety Car
  * Note: Soccer event types include Goal, Penalty Goal, Red Card, Yellow Card, and Match End
- 1.3.4. User saves configuration as Team Defaults
- 1.3.5. System validates entity IDs against Home Assistant and reports any unavailable entities

#### 1.4. Testing and Calibration

- 1.4.1. User navigates to Effect Tester
- 1.4.2. User selects a configured team and event type
- 1.4.3. User initiates manual test trigger
- 1.4.4. System executes light effects on selected entities and plays sound on selected media players
- 1.4.5. System fires `gamesync_score` event if enabled, allowing user to verify custom automation triggers
- 1.4.6. User confirms effects work as expected or adjusts configuration

### 2. Managing Teams and Auto-Sync

#### 2.1. Team Management Dashboard

- 2.1.1. User views list of all followed teams with current auto-sync status indicators
- 2.1.2. User toggles auto-sync setting per team (default off, as per hybrid approach)
- 2.1.3. User sets priority ranking for teams to resolve future conflicts (e.g., NFL Team A priority 1, NHL Team B priority 2)
- 2.1.4. User removes teams from followed list, archiving their configurations

#### 2.2. Default Effect Maintenance

- 2.2.1. User selects a team from management list to edit defaults
- 2.2.2. System loads existing TeamEventConfigurations
- 2.2.3. User modifies event mappings, changes target entities, or uploads new custom MP3 to Sound Library and assigns it
- 2.2.4. User saves updates, affecting all future games for that team unless overridden

### 3. Game-Specific Overrides

#### 3.1. Browsing Upcoming Games

- 3.1.1. User navigates to Game Browser showing schedule for next 14 days
- 3.1.2. System displays games involving followed teams, indicating:
  * Regular season vs. Playoff/Postseason status
  * Existing override configurations (if any)
  * Conflicting time slots with other followed teams
- 3.1.3. User filters view by league or team
- 3.1.4. User selects a specific game (e.g., Super Bowl, Playoff Game) to customize

#### 3.2. Creating Override Configuration

- 3.2.1. User toggles "Override Team Defaults" for selected game
- 3.2.2. System presents event mapping interface identical to Team Defaults configuration
- 3.2.3. User configures unique effects for this specific matchup (e.g., more intense strobing for championship games, different colors for rivalry games)
- 3.2.4. User adds optional note describing the override (e.g., "Super Bowl Party Mode")
- 3.2.5. System saves GameOverrideConfiguration linked to specific game instance
- 3.2.6. System indicates in Game Browser that this game has active overrides

#### 3.3. Managing Existing Overrides

- 3.3.1. User views list of upcoming games with overrides
- 3.3.2. User edits or deletes override configurations
- 3.3.3. System confirms deletion reverts game to Team Defaults for future events

### 4. Game Day Activation and Live Monitoring

#### 4.1. Manual Game Following

- 4.1.1. User opens Dashboard showing current and upcoming games
- 4.1.2. For games not in auto-sync mode, user clicks "Follow" to activate monitoring
- 4.1.3. System creates ActiveGameSession for that game with effects_enabled=true
- 4.1.4. If another game is already active, system prompts for priority resolution (see Journey 5)

#### 4.2. Automatic Game Detection

- 4.2.1. System polls sports APIs every N minutes (respecting rate limits)
- 4.2.2. When system detects a followed team with auto_sync_enabled=true has a game with status changed to "live", system automatically creates ActiveGameSession
- 4.2.3. If no other active sessions exist, session is marked as Primary (is_primary=true, effects execute)
- 4.2.4. If other sessions exist, system applies priority rules from Journey 5

#### 4.3. Live Event Processing

- 4.3.1. System detects score events for Primary game via API polling
- 4.3.2. System identifies event type (e.g., touchdown, home run)
- 4.3.3. System looks up configuration:
  * First checks GameOverrideConfiguration if exists for this game
  * Falls back to TeamEventConfiguration for the scoring team
  * Note: For F1 races, events are triggered via OpenF1 API polling with event-specific configurations
- 4.3.4. System executes configured light effects on target entities
- 4.3.5. System plays selected sound asset on target media players
- 4.3.6. System fires `gamesync_score` Home Assistant event with payload containing game_id, team_id, event_type, score_values, timestamp
- 4.3.7. System logs event processing timestamp to prevent duplicate triggers

#### 4.4. Monitoring Multiple Games

- 4.4.1. Dashboard displays all ActiveGameSessions with status indicators:
  * Primary game (effects active)
  * Secondary games (monitoring active, effects suppressed)
  * Upcoming auto-sync games (scheduled activation)
- 4.4.2. User can manually switch Primary status between live games if desired
- 4.4.3. System continues polling all active games but only executes effects for Primary session

### 5. Conflict Resolution and Priority Management

#### 5.1. Automatic Conflict Detection

- 5.1.1. When a second game involving a followed team begins while another ActiveGameSession exists:
- 5.1.2. System compares priority rankings of the two teams (from Team Management)
- 5.1.3. Higher priority team becomes/stays Primary; lower priority becomes Secondary
- 5.1.4. System sends notification to user interface indicating which game is now Primary and which is muted
- 5.1.5. Secondary game continues API polling and event detection but suppresses all light and sound executions

#### 5.2. Manual Override of Priority

- 5.2.1. User views Active Games list showing Primary and Secondary indicators
- 5.2.2. User selects Secondary game and clicks "Make Primary"
- 5.2.3. System updates ActiveGameSessions:
  * Demotes current Primary to Secondary (effects muted)
  * Promotes selected game to Primary (effects enabled)
- 5.2.4. System applies change immediately; next detected event in new Primary game triggers effects

#### 5.3. Game Completion Handling

- 5.3.1. When Primary game status changes to "final", system marks session as completed
- 5.3.2. If Secondary games exist, system automatically promotes highest priority Secondary game to Primary
- 5.3.3. System notifies user of promotion and begins executing effects for newly promoted game

### 6. Sound Asset Management

#### 6.1. Built-in Library Access

- 6.1.1. User navigates to Sound Library
- 6.1.2. System displays categorized built-in sounds (Horns, Cheers, Buzzers, Crowd Noise)
- 6.1.3. User previews sounds via browser audio playback
- 6.1.4. User selects built-in sounds for assignment in team or game configurations

#### 6.2. Custom Sound Upload

- 6.2.1. User selects "Upload Custom Sound"
- 6.2.2. User provides MP3 file from local system (file size limit enforced)
- 6.2.3. System validates file format and stores in add-on persistent storage
- 6.2.4. System makes custom sound available in selection lists alongside built-in sounds
- 6.2.5. User can delete custom uploads; built-in sounds are non-deletable

## Data Model

### League

Represents a professional sports league supported by the system.

**Fields:**
* `id`: Unique identifier
* `code`: Enum [`NFL`, `NBA`, `MLB`, `NHL`, `F1`, `PREMIER_LEAGUE`, `MLS`]
* `name`: Display name (e.g., "National Football League")
* `sport_type`: String (e.g., "football", "basketball")
* `api_endpoint`: String (URL pattern or identifier for free public API source)
* `polling_interval_minutes`: Integer (default 2, respects rate limits)
* `enabled`: Boolean (whether user has activated this league)

### Team

Represents a sports team within a league.

**Fields:**
* `id`: Unique identifier
* `league_id`: FK League
* `name`: Full team name (e.g., "New England Patriots")
* `abbreviation`: String (e.g., "NE")
* `city`: String (e.g., "New England")
* `primary_color_hex`: String (e.g., "#002244")
* `secondary_color_hex`: String (e.g., "#C60C30")
* `external_api_id`: String (identifier used by sports data API)

**Relationships:**
* Belongs to one `League`
* Referenced by many `FollowedTeam` entries

### FollowedTeam

Represents a user-subscribed team with configuration preferences.

**Fields:**
* `id`: Unique identifier
* `team_id`: FK Team
* `auto_sync_enabled`: Boolean (default false)
* `priority_rank`: Integer (1 is highest, used for conflict resolution)
* `created_at`: Timestamp

**Relationships:**
* Belongs to one `Team`
* Has many `TeamEventConfiguration` entries
* Has many `ActiveGameSession` entries

### Game

Represents a specific scheduled or live game.

**Fields:**
* `id`: Unique identifier
* `league_id`: FK League
* `home_team_id`: FK Team
* `away_team_id`: FK Team
* `scheduled_start_time`: Timestamp
* `status`: Enum [`scheduled`, `live`, `final`, `postponed`, `cancelled`]
* `current_period`: String (e.g., "Q2", "3rd Inning", "2nd Period")
* `time_remaining`: String (e.g., "2:34", "Top 5th")
* `score_home`: Integer (nullable)
* `score_away`: Integer (nullable)
* `is_playoffs`: Boolean
* `season_round`: String (e.g., "Week 12", "Wild Card", "Game 7")
* `external_api_game_id`: String
* `last_updated`: Timestamp

**Relationships:**
* Belongs to `League`, `Team` (home and away)
* Has one optional `GameOverrideConfiguration`
* Has many `ActiveGameSession` entries
* Has many `ScoreEvent` entries

### EventTypeDefinition

Template of possible scoring events per league.

**Fields:**
* `id`: Unique identifier
* `league_id`: FK League
* `event_code`: String (e.g., `touchdown`, `field_goal`, `home_run`, `three_pointer`)
* `display_name`: String (e.g., "Touchdown", "Home Run")
* `description`: String (optional help text)
* `point_value`: Integer (e.g., 6, 3, 1, 4)

**Relationships:**
* Belongs to `League`

### TeamEventConfiguration

Default effect configuration for a specific event type on a followed team.

**Fields:**
* `id`: Unique identifier
* `followed_team_id`: FK FollowedTeam
* `event_type_id`: FK EventTypeDefinition
* `light_effect_type`: Enum [`flash`, `strobe`, `pulse`, `solid`, `none`]
* `light_color_hex`: String (nullable, uses team color if null)
* `target_light_entities`: JSON array of Home Assistant entity_ids
* `sound_asset_id`: FK SoundAsset (nullable)
* `target_media_players`: JSON array of Home Assistant entity_ids
* `fire_ha_event`: Boolean (whether to fire `gamesync_score` event)
* `duration_seconds`: Integer (effect duration)
* `active`: Boolean (whether this mapping is enabled)

**Relationships:**
* Belongs to `FollowedTeam`
* Belongs to `EventTypeDefinition`
* Belongs to `SoundAsset` (optional)

### GameOverrideConfiguration

Specialized configuration overriding team defaults for a specific game.

**Fields:**
* `id`: Unique identifier
* `game_id`: FK Game
* `followed_team_id`: FK FollowedTeam (which team's perspective this config is for)
* `is_enabled`: Boolean
* `note`: String (user description, e.g., "Super Bowl Party Mode")
* `created_at`: Timestamp

**Relationships:**
* Belongs to `Game` and `FollowedTeam`
* Has many `GameOverrideEventConfiguration` entries

### GameOverrideEventConfiguration

Specific event effect overrides within a GameOverrideConfiguration. Mirrors `TeamEventConfiguration` but applies only to the specific game context.

**Fields:**
* `id`: Unique identifier
* `game_override_id`: FK GameOverrideConfiguration
* `event_type_id`: FK EventTypeDefinition
* `light_effect_type`: Enum [`flash`, `strobe`, `pulse`, `solid`, `none`, `inherit`]
* `light_color_hex`: String (nullable, or "inherit")
* `target_light_entities`: JSON array of Home Assistant entity_ids (or null to inherit)
* `sound_asset_id`: FK SoundAsset (nullable, or "inherit")
* `target_media_players`: JSON array of Home Assistant entity_ids (or null to inherit)
* `fire_ha_event`: Boolean (or "inherit")
* `duration_seconds`: Integer (or null to inherit)
* `active`: Boolean

**Relationships:**
* Belongs to `GameOverrideConfiguration`
* Belongs to `EventTypeDefinition`
* Belongs to `SoundAsset` (optional)

### SoundAsset

Audio files available for playback.

**Fields:**
* `id`: Unique identifier
* `name`: Display name (e.g., "Goal Horn", "Touchdown Cheer")
* `category`: Enum [`built_in`, `custom`]
* `file_path`: String (relative path in add-on storage)
* `content_type`: String (e.g., "audio/mpeg")
* `duration_seconds`: Integer
* `uploaded_at`: Timestamp (null for built-in)
* `file_size_bytes`: Integer

**Relationships:**
* Referenced by `TeamEventConfiguration` and `GameOverrideEventConfiguration`

### ActiveGameSession

Runtime state of a currently monitored game.

**Fields:**
* `id`: Unique identifier
* `game_id`: FK Game
* `followed_team_id`: FK FollowedTeam (which followed team caused this monitoring)
* `session_start_time`: Timestamp
* `is_primary`: Boolean (only primary sessions execute effects)
* `effects_enabled`: Boolean (allows temporary muting without stopping monitoring)
* `last_event_processed_at`: Timestamp
* `last_score_home`: Integer (cached to detect changes)
* `last_score_away`: Integer (cached to detect changes)

**Relationships:**
* Belongs to `Game` and `FollowedTeam`

### ScoreEvent

Record of detected scoring plays from API (used for deduplication and history).

**Fields:**
* `id`: Unique identifier
* `game_id`: FK Game
* `event_type_id`: FK EventTypeDefinition
* `scoring_team_id`: FK Team (which team scored)
* `points_scored`: Integer
* `game_time`: String (e.g., "14:32 Q2" from API)
* `detected_at`: Timestamp (when GameSync detected this)
* `processed`: Boolean (whether effects were triggered)
* `processing_session_id`: FK ActiveGameSession (which session handled it, if any)

**Relationships:**
* Belongs to `Game`, `EventTypeDefinition`, `Team`, `ActiveGameSession`

## Frontend

#### Primary Navigation

* GameSync brand identifier
* Navigation sections: Dashboard, Teams, Games, Sound Library, Settings
* Status indicator showing API connection health and rate limit status
* Active game counter (number of live games being monitored)

#### Global Controls

* Master mute toggle (temporarily disable all sounds without changing configurations)
* Emergency stop (immediately stops all active light effects)

#### Home Assistant Integration Bar

* Contextual indicator showing Home Assistant connection status
* Quick link to Home Assistant Developer Tools for users building custom automations on `gamesync_score` events

### DashboardScreen

Summary: Central status and control panel for game day operations, handling both onboarding for new users and live game monitoring for active users.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default (Standard Mode) | Displays the Standard Mode view with the Today's Schedule, Active Games section showing a Primary game and a Secondary game, and the Recent Activity log populated with sample score events.
ID: onboarding | Onboarding Mode | Displays the Onboarding Mode view where no teams are followed. Shows the League selection grid (NFL, NBA, MLB, NHL, F1, Premier League, MLS) with toggles and the "Next" button.
ID: conflictDetected | Conflict Detected | Similar to Default, but the Active Games section highlights a conflict scenario where two games are live, visually distinguishing which is Primary (effects active) and which is Secondary (muted).

#### Contents

Central status and control panel for game day operations. If no teams are followed, it serves as the entry point for Onboarding, allowing League selection.

**Content Hierarchy:**
  * **Onboarding Mode (if no teams followed):**
  * League selection grid (NFL, NBA, MLB, NHL, F1, Premier League, MLS) with toggle switches
  * "Next" button leading to Team Discovery
* **Standard Mode:**
  * Today's Schedule section showing games involving followed teams in next 24 hours
  * Active Games section with visual distinction between Primary and Secondary sessions
  * Quick actions to "Follow" upcoming games manually
  * Auto-sync status summary per team with toggle controls
  * Recent Activity log showing last 5 processed score events with timestamps
  * API status warning area displaying rate limit proximity or connection errors

### TeamManagementScreen

Summary: Interface for managing followed teams, allowing users to toggle auto-sync, set priority rankings, configure effects, or remove teams from the list.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default | Displays a list of followed teams with their logos, auto-sync toggles, and priority ranks. The "Add Team" button is visible at the bottom or top.
ID: removeConfirmation | Remove Team Confirmation | Displays the list of teams, but a confirmation modal or dialog is visible asking the user to confirm the removal of a specific team.

#### Contents

Interface for managing followed teams and their default behaviors.

**Content Hierarchy:**
* Grid or list of followed teams with team names, logos, and league badges
* Auto-sync toggle per team row
* Priority rank assignment interface (drag-and-drop or numeric input)
* "Configure Effects" action per team leading to Team Configuration
* "Remove" action with confirmation for unfollowing teams
* "Add Team" button leading to Team Discovery interface

### TeamConfigurationScreen

Summary: Detailed setup screen for configuring default celebration behaviors, mapping event types to specific light patterns, colors, sounds, and Home Assistant entities.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default | Displays the Team header and the list of event types. One event type panel is expanded showing the Light effect selector, Color picker, Entity selectors, Sound selector, and HA Event toggle.
ID: testTrigger | Test Trigger Active | Similar to Default, but visual feedback indicates that the "Test Trigger" button has been pressed (e.g., a spinner or "Triggering..." status) for one of the event types.
ID: copyConfig | Copy Configuration | A modal or dropdown is visible allowing the user to select another team to copy the current configuration to.

#### Contents

Detailed setup for default celebration behaviors per event type.

**Content Hierarchy:**
* Team header showing name, colors, and league
* Event type list specific to team's league (e.g., Touchdown, Field Goal for NFL)
* Per event type configuration panel containing:
  * Light effect selector (pattern options)
  * Color picker (defaulting to team colors)
  * Home Assistant entity selectors for target lights
  * Sound asset selector (searchable, showing built-in and custom)
  * Home Assistant entity selectors for target media players
  * Toggle for firing Home Assistant events
  * Test trigger button for individual event type
* Global save action for all event types
* Copy configuration option to duplicate settings to another team

### TeamDiscoveryScreen

Summary: Searchable grid interface for discovering and following new teams from the enabled leagues.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default | Displays the grid of available teams with logos, names, and "Follow" buttons. The League filter tabs are visible, including tabs for Premier League and MLS.
ID: searchActive | Search Active | The search bar is focused and contains text. The team grid is filtered to show only matching results.
ID: followingStatus | Following Status Visible | The grid displays teams, some of which are marked as "Following" with "Unfollow" buttons, while others are "Not Following" with "Follow" buttons.

#### Contents

Interface for searching and following new teams. Accessible during onboarding or from the Team Management page.

**Content Hierarchy:**
* Header with "Add Teams" title
* League filter tabs or dropdown (restricted to leagues enabled in Settings; includes Premier League and MLS tabs)
* Search bar to filter teams by name, city, or abbreviation
* Grid or list of available teams displaying:
  * Team Logo
  * Team Name and City
  * League badge
  * Status indicator (Following / Not Following)
* Action buttons per team: "Follow" or "Unfollow"
* "Done" or "Finish" button to return to previous screen (Dashboard or Team Management)

### GameBrowserScreen

Summary: Calendar view of upcoming games allowing users to check schedules, view conflicts, and create specific override configurations.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default | Displays the list of upcoming games grouped by date headers. Games show teams, times, and "Configure" buttons.
ID: filterActive | Filters Applied | The filter controls (League and Team) are visible and active, filtering the game list to specific criteria.
ID: gameWithOverride | Game With Override | The game list is visible, and at least one game item displays the "Override status indicator" showing that a custom configuration exists for it.
ID: conflictWarning | Conflict Warning Visible | A game item in the list displays the "Conflict warning icon", indicating a scheduling overlap with another followed team.

#### Contents

Calendar and list view of upcoming matchups for planning overrides.

**Content Hierarchy:**
* Date range selector (default next 7 days, expandable)
* Filter controls for league and team
* Game list items displaying:
  * Teams and logos with record/standing if available
  * Scheduled time with countdown
  * Playoff/Regular season indicator
  * Override status indicator (has custom config or uses defaults)
  * Conflict warning icon if overlapping with another followed team game
  * "Configure" action leading to Game Override Editor
* Grouping by date headers

### GameOverrideEditorScreen

Summary: Configuration screen for creating or editing game-specific effect overrides, allowing unique behaviors for special matchups.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default | The Override toggle is enabled (On). The Note field is empty, and the event configuration panels are visible, pre-populated with team defaults.
ID: disabled | Override Disabled | The Override toggle is disabled (Off). The configuration panels are greyed out or hidden, indicating that team defaults will be used.
ID: deleteConfirmation | Delete Override Confirmation | A confirmation dialog is visible asking the user to confirm the deletion of the existing override configuration.

#### Contents

Specialized configuration for single-game custom effects.

**Content Hierarchy:**
* Game header showing matchup, time, and playoff status
* Toggle to enable/disable override (revert to team defaults when off)
* Note/description text field for user context
* Event configuration panels identical to Team Configuration, pre-populated with team defaults but editable
* Visual indicator showing which settings differ from team defaults
* Save and Cancel actions
* Delete override option (if editing existing)

### EffectTesterScreen

Summary: Calibration tool for manually triggering effects to verify light and media player configurations and connectivity.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default | Displays the Team and Event selectors, the "Trigger Test" button, and an empty Execution log.
ID: triggered | Test Triggered | The "Trigger Test" button has been pressed. The Execution log is populated with entries showing targeted light entities, media players, and the Home Assistant event payload.
ID: stopped | Effects Stopped | The user has clicked "Stop all effects". The Execution log shows a message indicating that effects were halted.

#### Contents

Calibration interface for verifying hardware setup without waiting for live games.

**Content Hierarchy:**
* Team selector (followed teams only)
* Event type selector (populated based on team's league)
* "Trigger Test" primary action
* Execution log showing:
  * Light entities targeted and response status
  * Media players targeted and response status
  * Home Assistant event fired confirmation with JSON payload preview
* Volume control for test sounds
* Stop all effects button (in case of runaway strobes)

### SoundLibraryScreen

Summary: Library for managing audio assets, allowing users to browse built-in sounds or upload custom MP3s for use in game events.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Built-in Tab | The "Built-in" tab is active. Displays categorized lists of sounds with play buttons, duration, and assignment counts.
ID: customTab | Custom Tab | The "Custom" tab is active. Displays the upload interface and a list of previously uploaded sounds with metadata and delete options.
ID: uploading | Uploading Sound | The upload interface is active, showing a drag-and-drop zone or file picker, possibly with a progress indicator for an active upload.

#### Contents

Management interface for audio assets.

**Content Hierarchy:**
* Tab or section switcher between "Built-in" and "Custom"
* Built-in section:
  * Categorized list (Horns, Cheers, Buzzers, Ambient)
  * Preview/play buttons for each sound
  * Duration display
  * Assignment count (how many configurations use this sound)
* Custom section:
  * Upload interface with drag-and-drop or file picker, MP3 validation
  * List of uploaded sounds with metadata (upload date, size)
  * Delete actions for custom sounds (with usage warnings if assigned to configurations)
  * Preview capability for uploaded sounds

### SettingsScreen

Summary: System configuration screen for managing data sources, league preferences, global effect defaults, storage, and advanced options.

Preview size: 1920x1080

#### Preview states

State | Name | Description
------|------|--------------------------------
ID: default | Default | Displays the Data Source section, League toggles, Global Effect Defaults, and Storage management. The Advanced section is collapsed.
ID: advancedExpanded | Advanced Section Expanded | The Advanced section is expanded, revealing the Home Assistant event name customization, Debug logging toggle, and API cache clear options.

#### Contents

System configuration and maintenance.

**Content Hierarchy:**
  * Data Source section showing current free API status, polling intervals, and rate limit warnings
  * League toggles to enable/disable entire leagues (affects API polling load; includes toggles for Premier League and MLS)
  * F1 API endpoint configuration (OpenF1)
* Global Effect Defaults:
  * Maximum strobe duration safety limit
  * Default light brightness level
  * Sound volume normalization option
* Storage management showing custom sound storage usage
* Advanced section:
  * Home Assistant event name customization (default: `gamesync_score`)
  * Debug logging toggle
  * Manual API cache clear
* System info showing version and last successful data fetch timestamp