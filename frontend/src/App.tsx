/**
 * JAWIR OS — Main Application
 * WebSocket message handler, tab routing, layout orchestration
 */

import { useCallback, useRef, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useChatStore, useAgentStore, useUIStore, useIoTStore } from '@/stores';
import {
  Header,
  Sidebar,
  ChatPanel,
  ReActPanel,
  ToolsPanel,
  DashboardPanel,
  IoTPanel,
  FileUpload,
  SettingsModal,
  FireAlert,
} from '@/components';
import type { WSMessage, AgentStatus } from '@/types';

export default function App() {
  const { addMessage } = useChatStore();
  const { setConnected, setStatus, startIteration, addReActStep, addToolResult } = useAgentStore();
  const { activeTab, fireAlert, showFireAlert, hideFireAlert } = useUIStore();
  const { updateDevice, devices } = useIoTStore();
  
  // Track previous flame states to detect changes
  const prevFlameStates = useRef<Record<string, boolean>>({});

  /**
   * Central WebSocket message handler
   * Maps backend message types to store actions
   */
  const handleMessage = useCallback(
    (msg: WSMessage) => {
      // Helper to safely access flat message fields
      const field = (key: string) => (msg as Record<string, unknown>)[key];
      const fieldStr = (key: string) => (field(key) as string) || '';
      const fieldObj = (key: string) => (field(key) as Record<string, unknown>) || {};
      const fieldNum = (key: string, def: number) => (field(key) as number) ?? def;

      switch (msg.type) {
        // Connection established
        case 'connection': {
          setConnected(true);
          setStatus('idle', fieldStr('message') || 'Terhubung');
          break;
        }

        // Agent status changed (thinking, planning, executing_tool, etc.)
        case 'agent_status': {
          const status = fieldStr('status') as AgentStatus;
          const message = fieldStr('message');
          const details = fieldObj('details');
          setStatus(status, message);

          // Handle iteration_start as sub-status
          if (status === 'iteration_start') {
            startIteration(
              (details.iteration as number) || 1,
              (details.max as number) || 10
            );
          }

          // Also push as a ReAct step
          if (status && status !== 'idle' && status !== 'done') {
            addReActStep({
              type: status,
              content: message,
              toolName: fieldStr('tool_name') || (details.tool_name as string),
              timestamp: Date.now(),
            });
          }
          break;
        }

        // Iteration start from backend ReAct loop (also handled in agent_status)
        case 'iteration_start': {
          startIteration(
            fieldNum('iteration', 1),
            fieldNum('max_iterations', 10)
          );
          break;
        }

        // Tool execution result
        case 'tool_result': {
          const toolId = fieldStr('tool_call_id') || crypto.randomUUID();
          const toolData = fieldObj('data');
          addToolResult({
            id: toolId,
            toolName: fieldStr('tool_name') || 'unknown',
            status: fieldStr('status') || 'success',
            title: (toolData.title as string) || fieldStr('tool_name') || '',
            summary: (toolData.summary as string) || '',
            data: toolData,
            duration: field('duration') as number | undefined,
            timestamp: Date.now(),
          });

          // Also add as ReAct step
          addReActStep({
            type: 'executing_tool',
            content: (toolData.summary as string) || `Tool: ${fieldStr('tool_name')}`,
            toolName: fieldStr('tool_name'),
            result: toolData,
            duration: field('duration') as number | undefined,
            timestamp: Date.now(),
          });
          break;
        }

        // Final agent response — backend sends content at top level
        case 'agent_response': {
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: fieldStr('content') || fieldStr('response') || '',
            timestamp: Date.now(),
          });

          // Add "done" step to ReAct
          addReActStep({
            type: 'done',
            content: 'Agent selesai merespon',
            timestamp: Date.now(),
          });

          // Reset status to idle
          setStatus('idle', '');
          break;
        }

        // Streaming text (partial response)
        case 'stream': {
          // Could implement streaming text updates here
          // For now, we'll just track it as a status
          if (fieldStr('text')) {
            setStatus('writing', 'Menulis respon...');
          }
          break;
        }

        // Error from backend
        case 'error': {
          addMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: `⚠️ Error: ${fieldStr('message') || fieldStr('error') || 'Terjadi kesalahan'}`,
            timestamp: Date.now(),
          });

          addReActStep({
            type: 'error',
            content: fieldStr('message') || fieldStr('error') || 'Error',
            timestamp: Date.now(),
          });

          setStatus('error', fieldStr('message') || 'Error');

          // Auto-reset to idle after 3s
          setTimeout(() => setStatus('idle', ''), 3000);
          break;
        }

        // Pong response (heartbeat)
        case 'pong': {
          // Just confirm connection alive — no UI action needed
          break;
        }

        // Task cancelled
        case 'cancelled': {
          setStatus('idle', fieldStr('message') || 'Dibatalkan');
          addReActStep({
            type: 'done',
            content: fieldStr('message') || 'Task dibatalkan oleh user',
            timestamp: Date.now(),
          });
          break;
        }

        // Direct fire alert from backend - ALWAYS show popup
        case 'iot_fire_alert': {
          const deviceName = fieldStr('device_name') || 'Detektor Api';
          const room = fieldStr('room') || 'Unknown Room';
          const alertMessage = fieldStr('message') || 'API terdeteksi!';
          
          // Show fire alert popup immediately
          showFireAlert(deviceName, room);
          
          // Add message to chat
          addMessage({
            id: `fire-alert-${Date.now()}`,
            role: 'assistant',
            type: 'done',
            content: `🔥🚨 **AWAS GENI!** ${alertMessage}\n\n**Device:** ${deviceName}\n**Lokasi:** ${room}\n\n⚠️ Segera evakuasi area dan hubungi pemadam kebakaran!`,
            timestamp: Date.now(),
          });
          break;
        }

        // IoT device update from MQTT via WebSocket
        case 'iot_device_update': {
          const device = field('device') as Record<string, unknown> | undefined;
          if (device && device.device_id) {
            const deviceId = device.device_id as string;
            const flameDetected = device.flame_detected as boolean | undefined;
            const alarmActive = device.alarm_active as boolean | undefined;
            const deviceName = device.name as string || 'Unknown Device';
            const room = device.room as string || 'Unknown Room';
            
            // Fire alert triggers on either flame_detected OR alarm_active
            const isFireNow = flameDetected === true || alarmActive === true;
            const prevFlame = prevFlameStates.current[deviceId] ?? false;
            
            // Check if fire/alarm just became active (was false, now true)
            if (isFireNow && !prevFlame) {
              // Fire detected! Show alert and add chat message
              showFireAlert(deviceName, room);
              addMessage({
                id: `fire-alert-${Date.now()}`,
                role: 'assistant',
                type: 'done',
                content: `🔥🚨 **AWAS GENI!** API TERDETEKSI!\n\n**Device:** ${deviceName}\n**Lokasi:** ${room}\n\n⚠️ Segera evakuasi area dan hubungi pemadam kebakaran!`,
                timestamp: Date.now(),
              });
            }
            
            // Update fire state tracker
            prevFlameStates.current[deviceId] = isFireNow;
            
            updateDevice({
              device_id: deviceId,
              name: deviceName,
              device_type: (device.device_type as 'fan' | 'fire_detector') || 'fan',
              room: room,
              online: device.online as boolean || false,
              last_seen: device.last_seen as string | null || null,
              mode: device.mode as 'manual' | 'auto' | undefined,
              speed: device.speed as 'off' | 'low' | 'med' | 'high' | undefined,
              temperature: device.temperature as number | null | undefined,
              humidity: device.humidity as number | null | undefined,
              gas_analog: device.gas_analog as number | undefined,
              flame_detected: flameDetected,
              alarm_active: device.alarm_active as boolean | undefined,
            });
          }
          break;
        }

        default: {
          console.log('[WS] Unhandled message type:', msg.type, msg);
        }
      }
    },
    [addMessage, setConnected, setStatus, startIteration, addReActStep, addToolResult, updateDevice, showFireAlert]
  );

  /**
   * Handle WebSocket connection state changes
   */
  const handleConnectionChange = useCallback((connected: boolean) => {
    setConnected(connected);
    if (!connected) {
      setStatus('disconnected', 'Koneksi terputus');
    }
  }, [setConnected, setStatus]);

  // Initialize WebSocket connection
  const wsUrl = 'ws://localhost:8000/ws/chat';
  const { sendMessage } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    onConnectionChange: handleConnectionChange,
  });

  // Render active tab panel
  const renderPanel = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPanel sendMessage={sendMessage} />;
      case 'react':
        return <ReActPanel />;
      case 'tools':
        return <ToolsPanel />;
      case 'dashboard':
        return <DashboardPanel />;
      case 'iot':
        return <IoTPanel />;
      default:
        return <ChatPanel sendMessage={sendMessage} />;
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-background-dark">
      {/* Header with Batik Trim */}
      <Header />

      {/* Main Layout: Sidebar + Content */}
      <div className="flex-1 flex min-h-0">
        <Sidebar />

        {/* Content Panel */}
        <main className="flex-1 flex flex-col min-h-0 bg-coffee-dark">
          {renderPanel()}
        </main>
      </div>

      {/* Modals */}
      <FileUpload />
      <SettingsModal />
      
      {/* Fire Alert Popup */}
      <FireAlert
        isVisible={fireAlert.isVisible}
        deviceName={fireAlert.deviceName}
        room={fireAlert.room}
        onDismiss={hideFireAlert}
      />
    </div>
  );
}
