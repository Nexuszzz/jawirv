/**
 * JAWIR OS — Sidebar Component
 * Navigation + Tool Categories + Quick Actions + Session Info
 */

import { useUIStore, useAgentStore, useSessionStore } from '@/stores';
import type { TabId } from '@/types';
import { TOOL_CATEGORIES } from '@/data/tools';

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: 'chat', label: 'Chat', icon: 'forum' },
  { id: 'react', label: 'ReAct Loop', icon: 'psychology' },
  { id: 'tools', label: 'Tools', icon: 'build' },
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'iot', label: 'IoT', icon: 'sensors' },
];

export default function Sidebar() {
  const { activeTab, setActiveTab, sidebarCollapsed, toggleSidebar } = useUIStore();
  const { isConnected, toolResults } = useAgentStore();
  const { sessionId } = useSessionStore();

  return (
    <aside className={`${sidebarCollapsed ? 'w-16' : 'w-[280px]'} flex-none bg-[#1c1912] border-r border-coffee-light flex flex-col transition-all duration-300`}>
      {/* Collapse toggle */}
      <div className="px-3 py-3 border-b border-coffee-light flex items-center justify-between">
        {!sidebarCollapsed && (
          <span className="text-xs font-bold text-cream-muted uppercase tracking-widest">Navigasi</span>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-cream-muted hover:text-white hover:bg-coffee-light transition-colors"
        >
          <span className="material-symbols-outlined text-lg">
            {sidebarCollapsed ? 'chevron_right' : 'chevron_left'}
          </span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <nav className="px-3 py-3 space-y-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${activeTab === tab.id
                ? 'bg-primary text-background-dark font-bold shadow-lg shadow-primary/20'
                : 'text-cream-muted hover:text-white hover:bg-coffee-light'
              }`}
          >
            <span className="material-symbols-outlined text-[22px]">{tab.icon}</span>
            {!sidebarCollapsed && <span className="text-sm">{tab.label}</span>}
            {/* Badge for tool results */}
            {tab.id === 'tools' && toolResults.length > 0 && !sidebarCollapsed && (
              <span className="ml-auto bg-primary/20 text-primary text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {toolResults.length}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Divider */}
      {!sidebarCollapsed && <div className="mx-5 border-t border-coffee-light" />}

      {/* Tool Categories */}
      {!sidebarCollapsed && (
        <div className="px-3 py-3 flex-1 overflow-y-auto">
          <span className="text-xs font-bold text-cream-muted uppercase tracking-widest px-3 mb-3 block">
            Tool Categories
          </span>
          <div className="space-y-0.5">
            {TOOL_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveTab('tools')}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-cream-muted hover:text-white hover:bg-coffee-light transition-colors group"
              >
                <span className={`material-symbols-outlined text-lg ${cat.color}`}>{cat.icon}</span>
                <span className="text-xs font-medium">{cat.name}</span>
                <span className="ml-auto text-[10px] text-cream-muted/50 group-hover:text-cream-muted">
                  {cat.tools.length}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Bottom: Connection info */}
      {!sidebarCollapsed && (
        <div className="mt-auto border-t border-coffee-light p-4">
          <div className="bg-coffee-medium rounded-xl p-3 border border-coffee-light">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="text-xs text-cream-muted font-medium">
                {isConnected ? 'Backend Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="text-[10px] text-cream-muted/60 font-mono truncate">
              Session: {sessionId.slice(0, 8)}...
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
