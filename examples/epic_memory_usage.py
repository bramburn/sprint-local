import asyncio
from memory import NavigatorMemorySaver

async def demonstrate_epic_management():
    """
    Demonstrate the usage of epic management features in NavigatorMemorySaver.
    """
    # Initialize the memory saver
    memory_saver = NavigatorMemorySaver()

    # 1. Adding a new epic
    print("1. Adding a new epic...")
    await memory_saver.add_epic(
        epic_id="refactor_authentication",
        content={
            "title": "Refactor Authentication System",
            "description": "Improve the current authentication flow",
            "priority": "high",
            "assignee": "dev_team"
        }
    )

    # 2. Retrieve pending epics
    print("\n2. Retrieving pending epics...")
    pending_epics = await memory_saver.get_pending_epics()
    for epic in pending_epics:
        print(f"Epic ID: {epic['id']}")
        print(f"Content: {epic['content']}")
        print(f"Status: {epic['status']}")
        print(f"Created At: {epic['created_at']}")

    # 3. Update epic status
    print("\n3. Updating epic status...")
    await memory_saver.update_epic_status(
        epic_id="refactor_authentication", 
        status="in_progress"
    )

    # 4. Add another epic to demonstrate multi-epic handling
    print("\n4. Adding another epic...")
    await memory_saver.add_epic(
        epic_id="improve_error_handling",
        content={
            "title": "Improve Error Handling",
            "description": "Create more detailed error messages",
            "priority": "medium",
            "assignee": "backend_team"
        }
    )

    # 5. Retrieve all pending epics again
    print("\n5. Retrieving updated pending epics...")
    pending_epics = await memory_saver.get_pending_epics()
    for epic in pending_epics:
        print(f"Epic ID: {epic['id']}")
        print(f"Content: {epic['content']}")
        print(f"Status: {epic['status']}")

    # 6. Demonstrate thread-specific epic management
    print("\n6. Adding thread-specific epics...")
    await memory_saver.add_epic(
        epic_id="frontend_redesign",
        content={
            "title": "Frontend UI Redesign",
            "description": "Modernize the user interface",
            "priority": "low"
        },
        thread_id="frontend_project"
    )

    # 7. Retrieve thread-specific epics
    print("\n7. Retrieving thread-specific epics...")
    frontend_epics = await memory_saver.get_pending_epics(thread_id="frontend_project")
    for epic in frontend_epics:
        print(f"Thread Epic ID: {epic['id']}")
        print(f"Content: {epic['content']}")

    # 8. Clear completed epics
    print("\n8. Clearing completed epics...")
    await memory_saver.update_epic_status(
        epic_id="refactor_authentication", 
        status="completed"
    )
    await memory_saver.clear_completed_epics()

    # 9. Verify remaining epics
    print("\n9. Verifying remaining epics...")
    remaining_epics = await memory_saver.get_pending_epics()
    print(f"Number of remaining pending epics: {len(remaining_epics)}")

# Run the demonstration
if __name__ == "__main__":
    asyncio.run(demonstrate_epic_management())
