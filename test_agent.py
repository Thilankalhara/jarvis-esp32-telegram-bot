import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pc_agent.tools import system_tools, file_tools, web_tools, dev_tools, doc_tools

def run_local_test():
    print("="*60)
    print(" [J.A.R.V.I.S. LOCAL HARDWARE & SYSTEM TOOLS TESTER]")
    print("="*60)
    
    # 1. System Info Test
    print("\n[1] Testing System Info & Telemetry...")
    info = system_tools.get_system_info()
    print(f"    CPU Usage : {info.get('cpu_usage_percent')}%")
    print(f"    RAM Used  : {info.get('ram_used_gb')} GB / {info.get('ram_total_gb')} GB")
    print(f"    Disk Free : {info.get('disk_free_gb')} GB")
    
    # 2. Screenshot Test
    print("\n[2] Testing Desktop Screenshot Capture...")
    shot_path = system_tools.take_screenshot()
    print(f"    Screenshot saved to: {shot_path}")
    
    # 3. File Search & List Test
    print("\n[3] Testing File Manager...")
    desktop_files = file_tools.list_directory()
    print(f"    Found {len(desktop_files)} items on Desktop.")
    
    # 4. Word Document Generation Test
    print("\n[4] Testing Word Document Generator...")
    doc_path = doc_tools.create_word_document(
        title="J.A.R.V.I.S Test Document",
        content_sections=[
            {"heading": "System Initialization", "body": "All remote PC automation tools have been initialized successfully."},
            {"heading": "Hardware Node Status", "body": "ESP32 Wake-on-LAN listener ready for incoming magic packets."}
        ],
        output_filename="JARVIS_Test.docx"
    )
    print(f"    Generated test document: {doc_path}")

    print("\n" + "="*60)
    print(" [OK] LOCAL COMPONENT TEST COMPLETED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    run_local_test()
