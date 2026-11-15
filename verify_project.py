#!/usr/bin/env python3
import sys
import os

# Change to project directory
os.chdir('Z:/horgame/f1/rag')
sys.path.insert(0, 'backend')

print('=== PROJECT STRUCTURE VERIFICATION ===')
print()

# Check key files
key_files = [
    'backend/app/main.py',
    'backend/app/core/rag_logic.py',
    'backend/app/services/document_loader.py',
    'backend/app/services/cleanup_service.py',
    'backend/app/agents/web_browser.py',
    'backend/app/agents/api_caller.py',
    'backend/app/agents/memory.py',
    'frontend/index.html',
    'frontend/script.js',
    'frontend/style.css',
    'frontend/src/types.ts',
    'docker-compose.yml',
    'backend/Dockerfile',
    'nginx.conf',
    'memory/user.md',
    'memory/architecture.md',
]

all_ok = True
for f in key_files:
    exists = os.path.exists(f)
    status = 'OK' if exists else 'MISSING'
    if not exists:
        all_ok = False
    print(f'  [{status}] {f}')

print()
memory_dir = 'memory'
memory_count = len(os.listdir(memory_dir)) if os.path.exists(memory_dir) else 0
print(f'Memory directory: {memory_count} files')
print(f'All files present: {all_ok}')
print()

# Test imports
print('=== IMPORT TEST ===')
try:
    from app.main import app
    print('  OK backend/app/main.py')

    from app.agents.web_browser import WebBrowserAgent
    from app.agents.api_caller import ApiToolCallingAgent
    from app.agents.memory import LongTermMemoryAgent
    print('  OK all agent modules')

    import asyncio

    async def test():
        web = WebBrowserAgent()
        await web.initialize()
        print(f'  OK WebBrowserAgent.ready={web.is_ready()}')

        api = ApiToolCallingAgent()
        await api.initialize()
        print(f'  OK ApiToolCallingAgent.ready={api.is_ready()}')

        mem = LongTermMemoryAgent()
        await mem.initialize()
        print(f'  OK LongTermMemoryAgent.ready={mem.is_ready()}')

        await mem.store('test_key', {'test': 'value'})
        val = await mem.retrieve('test_key')
        print(f'  OK Memory store/retrieve={val is not None}')

        q = await mem.query('test_key')
        print(f'  OK Memory query={q["total_matches"]} matches')

        await api.close()
        await mem.clear()

    asyncio.run(test())
    print()
    print('=== ALL TESTS PASSED ===')
except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)