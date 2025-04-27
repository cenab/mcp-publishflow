# Substack Publishing Automation Architecture Plan

**Objective:** Architect a robust and systematic code solution for automating content publishing to Substack via browser automation using Playwright, triggered by a new MCP tool.

**Current State:**
*   A basic `SubstackPublisher` class exists (`publishers/substack_publisher.py`), but it only prepares manual instructions.
*   The MCP server (`mcp_publish_server.py`) is set up to register tools and publishers.
*   A `mcp_tools/substack_tools.py` file exists, likely intended for Substack-related MCP tools.

**Proposed Plan:**

1.  **Refactor `SubstackPublisher`**:
    *   Modify the `SubstackPublisher` class (`publishers/substack_publisher.py`) to use Playwright.
    *   Add methods for browser initialization, login, navigating to the new post page, filling in title, subtitle, and content, handling paid/free settings, and clicking the publish button.
    *   The `prepare_post` method will be replaced or adapted to work with the automation flow.
    *   Implement error handling for browser automation steps (e.g., element not found, login failure).
    *   Add necessary imports for Playwright.

2.  **Add Playwright Dependency**:
    *   Add `playwright` to the `requirements.txt` file.
    *   Include instructions for installing Playwright browsers (e.g., `playwright install`).

3.  **Create New MCP Tool**:
    *   Define a new asynchronous function in `mcp_tools/substack_tools.py` (e.g., `publish_substack_post_tool`).
    *   Decorate this function with `@mcp.tool` to register it with the server.
    *   This tool will accept parameters like `file_path` (for the content), `title`, `subtitle`, `is_paid`, and potentially scheduling information if needed later (though the current request is for trigger-based publishing).
    *   Inside the tool function, it will call the appropriate methods on the refactored `SubstackPublisher` instance to perform the automation.
    *   Include logging and error handling, reporting success or failure via the MCP tool response.

4.  **Integrate New Tool**:
    *   In `mcp_publish_server.py`, ensure the `register_substack_tools` function (or a new function if needed) correctly registers the `publish_substack_post_tool` with the `FastMCP` instance.
    *   Pass the initialized `SubstackPublisher` instance to the tool registration function.

5.  **Update Configuration**:
    *   Add new configuration variables to `config.py` for Substack login credentials (username, password) and Playwright settings (e.g., `PLAYWRIGHT_BROWSER`, `PLAYWRIGHT_HEADLESS`).
    *   Add corresponding entries to `.env.example`.

6.  **Implement Scheduling/Triggering**:
    *   Since the user chose triggering via a new MCP tool, the scheduling logic will reside in whatever system calls this new MCP tool. The MCP server itself will not handle scheduling internally based on this plan.

7.  **Testing**:
    *   Develop unit tests for the `SubstackPublisher` methods (mocking browser interactions where necessary).
    *   Develop integration tests to verify the entire flow from calling the MCP tool to successful (or failed) publishing via Playwright.

**Architectural Flow:**

```mermaid
graph TD
    A[External System/User] --> B(Call MCP Tool: publish_substack_post);
    B --> C[MCP Server];
    C --> D[mcp_tools/substack_tools.py];
    D --> E[publishers/SubstackPublisher];
    E --> F[Playwright];
    F --> G[Substack Website];
    G --> H{Publish Content};
    H --> I[Substack Website];
    I --> E;
    E --> D;
    D --> C;
    C --> B;
    B --> A[External System/User];

    %% Styling
    classDef default fill:#f9f,stroke:#333,stroke-width:2px;
    classDef tool fill:#ccf,stroke:#333,stroke-width:2px;
    classDef publisher fill:#cfc,stroke:#333,stroke-width:2px;
    classDef library fill:#ffc,stroke:#333,stroke-width:2px;
    classDef external fill:#eee,stroke:#333,stroke-width:2px;

    A:::external;
    B:::tool;
    C:::default;
    D:::default;
    E:::publisher;
    F:::library;
    G:::external;
    I:::external;