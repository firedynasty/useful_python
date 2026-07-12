import zipfile
from datetime import datetime

def create_xmind_from_xml(xml_content, output_filename):
    """Convert XML content to XMind file"""
    
    # Required files for XMind format
    files = {
        'content.xml': xml_content.encode('utf-8'),
        'META-INF/manifest.xml': '''<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
    <file-entry full-path="content.xml" media-type="text/xml"/>
</manifest>'''.encode('utf-8'),
        'meta.xml': f'''<?xml version="1.0" encoding="UTF-8"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
    <Author>Computer Systems Study Guide</Author>
    <Create-Time>{datetime.now().isoformat()}</Create-Time>
</meta>'''.encode('utf-8')
    }
    
    # Create ZIP file with .xmind extension
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)
    
    print(f"XMind file created: {output_filename}")

# Chapter 1.2 Computer Systems Hardware and Software XML content
xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" version="2.0">
    <sheet id="sheet1" theme="theme1">
        <topic id="root" structure-class="org.xmind.ui.map">
            <title>Chapter 1.2: Computer Systems Hardware &amp; Software</title>
            <children>
                <topics type="attached">
                    <topic id="cpu">
                        <title>Central Processing Unit (CPU)</title>
                        <children>
                            <topics type="attached">
                                <topic id="fetch-decode-execute">
                                    <title>Fetch-Decode-Execute Cycle</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="fetch">
                                                <title>FETCH</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="fetch-detail">
                                                            <title>Retrieve instruction from memory</title>
                                                        </topic>
                                                        <topic id="program-counter">
                                                            <title>Program Counter points to next instruction</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="decode">
                                                <title>DECODE</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="decode-detail">
                                                            <title>Interpret instruction format</title>
                                                        </topic>
                                                        <topic id="control-unit">
                                                            <title>Control unit determines operation</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="execute">
                                                <title>EXECUTE</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="execute-detail">
                                                            <title>Perform the operation</title>
                                                        </topic>
                                                        <topic id="alu">
                                                            <title>ALU handles arithmetic/logic operations</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="cpu-components">
                                    <title>CPU Components</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="control-unit-comp">
                                                <title>Control Unit</title>
                                            </topic>
                                            <topic id="alu-comp">
                                                <title>Arithmetic Logic Unit (ALU)</title>
                                            </topic>
                                            <topic id="registers">
                                                <title>Registers (fast temporary storage)</title>
                                            </topic>
                                            <topic id="cache">
                                                <title>Cache Memory (L1, L2, L3)</title>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                            </topics>
                        </children>
                    </topic>
                    <topic id="memory-systems">
                        <title>Memory Systems</title>
                        <children>
                            <topics type="attached">
                                <topic id="primary-memory">
                                    <title>Primary Memory (RAM)</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="ram-characteristics">
                                                <title>RAM Characteristics</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="volatile">
                                                            <title>Volatile (loses data when power off)</title>
                                                        </topic>
                                                        <topic id="random-access">
                                                            <title>Random access (any location accessible)</title>
                                                        </topic>
                                                        <topic id="fast-access">
                                                            <title>Fast read/write speeds</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="ram-types">
                                                <title>RAM Types</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="ddr4">
                                                            <title>DDR4 SDRAM</title>
                                                        </topic>
                                                        <topic id="ddr5">
                                                            <title>DDR5 SDRAM (newer, faster)</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="memory-hierarchy">
                                                <title>Memory Hierarchy</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="registers-hier">
                                                            <title>Registers (fastest, smallest)</title>
                                                        </topic>
                                                        <topic id="cache-hier">
                                                            <title>Cache Memory</title>
                                                        </topic>
                                                        <topic id="main-memory">
                                                            <title>Main Memory (RAM)</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="secondary-storage">
                                    <title>Secondary Storage</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="storage-comparison">
                                                <title>Solid-State vs Traditional Storage</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="ssd">
                                                            <title>Solid-State Drives (SSD)</title>
                                                            <children>
                                                                <topics type="attached">
                                                                    <topic id="ssd-pros">
                                                                        <title>Advantages</title>
                                                                        <children>
                                                                            <topics type="attached">
                                                                                <topic id="ssd-speed">
                                                                                    <title>Faster access times</title>
                                                                                </topic>
                                                                                <topic id="ssd-durability">
                                                                                    <title>More durable (no moving parts)</title>
                                                                                </topic>
                                                                                <topic id="ssd-power">
                                                                                    <title>Lower power consumption</title>
                                                                                </topic>
                                                                                <topic id="ssd-silent">
                                                                                    <title>Silent operation</title>
                                                                                </topic>
                                                                            </topics>
                                                                        </children>
                                                                    </topic>
                                                                    <topic id="ssd-cons">
                                                                        <title>Disadvantages</title>
                                                                        <children>
                                                                            <topics type="attached">
                                                                                <topic id="ssd-cost">
                                                                                    <title>Higher cost per GB</title>
                                                                                </topic>
                                                                                <topic id="ssd-lifespan">
                                                                                    <title>Limited write cycles</title>
                                                                                </topic>
                                                                            </topics>
                                                                        </children>
                                                                    </topic>
                                                                </topics>
                                                            </children>
                                                        </topic>
                                                        <topic id="hdd">
                                                            <title>Hard Disk Drives (HDD)</title>
                                                            <children>
                                                                <topics type="attached">
                                                                    <topic id="hdd-pros">
                                                                        <title>Advantages</title>
                                                                        <children>
                                                                            <topics type="attached">
                                                                                <topic id="hdd-cost">
                                                                                    <title>Lower cost per GB</title>
                                                                                </topic>
                                                                                <topic id="hdd-capacity">
                                                                                    <title>Higher storage capacities</title>
                                                                                </topic>
                                                                                <topic id="hdd-longevity">
                                                                                    <title>Proven long-term reliability</title>
                                                                                </topic>
                                                                            </topics>
                                                                        </children>
                                                                    </topic>
                                                                    <topic id="hdd-cons">
                                                                        <title>Disadvantages</title>
                                                                        <children>
                                                                            <topics type="attached">
                                                                                <topic id="hdd-speed">
                                                                                    <title>Slower access times</title>
                                                                                </topic>
                                                                                <topic id="hdd-mechanical">
                                                                                    <title>Mechanical parts (fragile)</title>
                                                                                </topic>
                                                                                <topic id="hdd-noise">
                                                                                    <title>Noise and heat generation</title>
                                                                                </topic>
                                                                                <topic id="hdd-power">
                                                                                    <title>Higher power consumption</title>
                                                                                </topic>
                                                                            </topics>
                                                                        </children>
                                                                    </topic>
                                                                    <topic id="hdd-components">
                                                                        <title>HDD Components</title>
                                                                        <children>
                                                                            <topics type="attached">
                                                                                <topic id="platters">
                                                                                    <title>Magnetic platters</title>
                                                                                </topic>
                                                                                <topic id="read-write-heads">
                                                                                    <title>Read/write heads</title>
                                                                                </topic>
                                                                                <topic id="actuator">
                                                                                    <title>Actuator arm</title>
                                                                                </topic>
                                                                                <topic id="spindle">
                                                                                    <title>Spindle motor</title>
                                                                                </topic>
                                                                            </topics>
                                                                        </children>
                                                                    </topic>
                                                                </topics>
                                                            </children>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="optical-storage">
                                                <title>Optical Storage</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="cd-dvd">
                                                            <title>CD/DVD/Blu-ray</title>
                                                        </topic>
                                                        <topic id="optical-characteristics">
                                                            <title>Read-only or writable formats</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                            </topics>
                        </children>
                    </topic>
                    <topic id="input-devices">
                        <title>Input Devices</title>
                        <children>
                            <topics type="attached">
                                <topic id="keyboard-mouse">
                                    <title>Traditional Input</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="keyboard">
                                                <title>Keyboard</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="mechanical-keyboard">
                                                            <title>Mechanical keyboards</title>
                                                        </topic>
                                                        <topic id="membrane-keyboard">
                                                            <title>Membrane keyboards</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="mouse">
                                                <title>Mouse</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="optical-mouse">
                                                            <title>Optical mouse</title>
                                                        </topic>
                                                        <topic id="laser-mouse">
                                                            <title>Laser mouse</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="disk-drives-input">
                                    <title>Disk Drives as Input</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="cd-rom">
                                                <title>CD-ROM drives</title>
                                            </topic>
                                            <topic id="dvd-drive">
                                                <title>DVD drives</title>
                                            </topic>
                                            <topic id="usb-drives">
                                                <title>USB flash drives</title>
                                            </topic>
                                            <topic id="external-storage">
                                                <title>External hard drives</title>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="other-input">
                                    <title>Other Input Devices</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="touchscreen">
                                                <title>Touchscreens</title>
                                            </topic>
                                            <topic id="microphone">
                                                <title>Microphones</title>
                                            </topic>
                                            <topic id="webcam">
                                                <title>Web cameras</title>
                                            </topic>
                                            <topic id="scanner">
                                                <title>Scanners</title>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                            </topics>
                        </children>
                    </topic>
                    <topic id="output-devices">
                        <title>Output Devices</title>
                        <children>
                            <topics type="attached">
                                <topic id="screens">
                                    <title>Display Screens</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="monitor-types">
                                                <title>Monitor Technologies</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="lcd">
                                                            <title>LCD (Liquid Crystal Display)</title>
                                                            <children>
                                                                <topics type="attached">
                                                                    <topic id="tn-panel">
                                                                        <title>TN panels (fast response)</title>
                                                                    </topic>
                                                                    <topic id="ips-panel">
                                                                        <title>IPS panels (better colors)</title>
                                                                    </topic>
                                                                    <topic id="va-panel">
                                                                        <title>VA panels (high contrast)</title>
                                                                    </topic>
                                                                </topics>
                                                            </children>
                                                        </topic>
                                                        <topic id="oled">
                                                            <title>OLED (Organic LED)</title>
                                                            <children>
                                                                <topics type="attached">
                                                                    <topic id="oled-benefits">
                                                                        <title>Perfect blacks, high contrast</title>
                                                                    </topic>
                                                                    <topic id="oled-drawbacks">
                                                                        <title>Potential burn-in issues</title>
                                                                    </topic>
                                                                </topics>
                                                            </children>
                                                        </topic>
                                                        <topic id="led">
                                                            <title>LED (Light Emitting Diode)</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="display-specs">
                                                <title>Display Specifications</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="resolution">
                                                            <title>Resolution (1080p, 1440p, 4K)</title>
                                                        </topic>
                                                        <topic id="refresh-rate">
                                                            <title>Refresh rate (60Hz, 144Hz, 240Hz)</title>
                                                        </topic>
                                                        <topic id="color-accuracy">
                                                            <title>Color accuracy and gamut</title>
                                                        </topic>
                                                        <topic id="response-time">
                                                            <title>Response time (ms)</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="audio-output">
                                    <title>Audio Output</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="speakers">
                                                <title>Speakers</title>
                                            </topic>
                                            <topic id="headphones">
                                                <title>Headphones</title>
                                            </topic>
                                            <topic id="sound-cards">
                                                <title>Sound cards/Audio interfaces</title>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="printers">
                                    <title>Printers</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="inkjet">
                                                <title>Inkjet printers</title>
                                            </topic>
                                            <topic id="laser">
                                                <title>Laser printers</title>
                                            </topic>
                                            <topic id="3d-printer">
                                                <title>3D printers</title>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                            </topics>
                        </children>
                    </topic>
                    <topic id="software-systems">
                        <title>Software Systems</title>
                        <children>
                            <topics type="attached">
                                <topic id="system-software">
                                    <title>System Software</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="operating-system">
                                                <title>Operating System (OS)</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="os-functions">
                                                            <title>OS Functions</title>
                                                            <children>
                                                                <topics type="attached">
                                                                    <topic id="process-management">
                                                                        <title>Process management</title>
                                                                    </topic>
                                                                    <topic id="memory-management">
                                                                        <title>Memory management</title>
                                                                    </topic>
                                                                    <topic id="file-system">
                                                                        <title>File system management</title>
                                                                    </topic>
                                                                    <topic id="device-drivers">
                                                                        <title>Device driver interface</title>
                                                                    </topic>
                                                                </topics>
                                                            </children>
                                                        </topic>
                                                        <topic id="os-types">
                                                            <title>OS Examples</title>
                                                            <children>
                                                                <topics type="attached">
                                                                    <topic id="windows">
                                                                        <title>Windows</title>
                                                                    </topic>
                                                                    <topic id="macos">
                                                                        <title>macOS</title>
                                                                    </topic>
                                                                    <topic id="linux">
                                                                        <title>Linux distributions</title>
                                                                    </topic>
                                                                </topics>
                                                            </children>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="compilers">
                                                <title>Compilers &amp; Interpreters</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="cpp-compiler">
                                                            <title>C++ Compilers (GCC, Clang, MSVC)</title>
                                                        </topic>
                                                        <topic id="compilation-process">
                                                            <title>Compilation process</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="application-software">
                                    <title>Application Software</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="programming-environments">
                                                <title>Programming Environments</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="ide">
                                                            <title>IDEs (Visual Studio, Code::Blocks)</title>
                                                        </topic>
                                                        <topic id="text-editors">
                                                            <title>Text editors</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                            <topic id="user-applications">
                                                <title>User Applications</title>
                                                <children>
                                                    <topics type="attached">
                                                        <topic id="productivity">
                                                            <title>Productivity software</title>
                                                        </topic>
                                                        <topic id="media-software">
                                                            <title>Media software</title>
                                                        </topic>
                                                        <topic id="games">
                                                            <title>Games</title>
                                                        </topic>
                                                    </topics>
                                                </children>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                            </topics>
                        </children>
                    </topic>
                    <topic id="programming-context">
                        <title>C++ Programming Context</title>
                        <children>
                            <topics type="attached">
                                <topic id="compilation-to-machine">
                                    <title>From Source to Execution</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="source-code">
                                                <title>C++ source code (.cpp files)</title>
                                            </topic>
                                            <topic id="preprocessing">
                                                <title>Preprocessing (#include, #define)</title>
                                            </topic>
                                            <topic id="compilation">
                                                <title>Compilation to object files</title>
                                            </topic>
                                            <topic id="linking">
                                                <title>Linking to executable</title>
                                            </topic>
                                            <topic id="execution">
                                                <title>CPU executes machine code</title>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                                <topic id="memory-in-cpp">
                                    <title>Memory Usage in C++</title>
                                    <children>
                                        <topics type="attached">
                                            <topic id="stack-memory">
                                                <title>Stack (local variables, function calls)</title>
                                            </topic>
                                            <topic id="heap-memory">
                                                <title>Heap (dynamic allocation with new/delete)</title>
                                            </topic>
                                            <topic id="program-memory">
                                                <title>Program memory (executable code)</title>
                                            </topic>
                                        </topics>
                                    </children>
                                </topic>
                            </topics>
                        </children>
                    </topic>
                </topics>
            </children>
        </topic>
    </sheet>
</xmap-content>'''

# Create the XMind file
create_xmind_from_xml(xml_content, "Chapter_1-2_Computer_Systems_Hardware_Software.xmind")

print("\nMind map created successfully!")
print("This comprehensive mind map covers:")
print("• CPU architecture and fetch-decode-execute cycle")
print("• Memory systems (RAM, cache hierarchy)")
print("• Storage comparison (SSD vs HDD)")
print("• Input devices (including disk drives)")
print("• Output devices (screens, audio, printers)")
print("• Software systems (OS, compilers, applications)")
print("• C++ programming context and memory usage")