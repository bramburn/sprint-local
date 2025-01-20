import pytest
import asyncio
from memory import NavigatorMemorySaver

@pytest.mark.asyncio
async def test_epic_management():
    """
    Test epic management methods in NavigatorMemorySaver.
    """
    memory_saver = NavigatorMemorySaver()
    
    # Add an epic
    await memory_saver.add_epic(
        epic_id="test_epic_1", 
        content={"description": "Test Epic 1"}
    )
    
    # Get pending epics
    pending_epics = await memory_saver.get_pending_epics()
    assert len(pending_epics) == 1
    assert pending_epics[0]['id'] == "test_epic_1"
    assert pending_epics[0]['status'] == "pending"
    
    # Update epic status
    await memory_saver.update_epic_status(
        epic_id="test_epic_1", 
        status="completed"
    )
    
    # Clear completed epics
    await memory_saver.clear_completed_epics()
    
    # Verify no pending epics
    pending_epics = await memory_saver.get_pending_epics()
    assert len(pending_epics) == 0

@pytest.mark.asyncio
async def test_multi_thread_epic_management():
    """
    Test epic management across different threads.
    """
    memory_saver = NavigatorMemorySaver()
    
    # Add epics to different threads
    await memory_saver.add_epic(
        epic_id="thread1_epic", 
        content={"description": "Thread 1 Epic"},
        thread_id="thread1"
    )
    
    await memory_saver.add_epic(
        epic_id="thread2_epic", 
        content={"description": "Thread 2 Epic"},
        thread_id="thread2"
    )
    
    # Get pending epics for each thread
    thread1_epics = await memory_saver.get_pending_epics(thread_id="thread1")
    thread2_epics = await memory_saver.get_pending_epics(thread_id="thread2")
    
    assert len(thread1_epics) == 1
    assert len(thread2_epics) == 1
    
    assert thread1_epics[0]['id'] == "thread1_epic"
    assert thread2_epics[0]['id'] == "thread2_epic"
