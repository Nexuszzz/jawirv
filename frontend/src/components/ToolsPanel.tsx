/**
 * JAWIR OS — Tools Panel
 * Grid display of all 30 tools across 13 categories
 */

import { useState } from 'react';
import { TOOL_CATEGORIES, TOOL_COUNT } from '@/data/tools';
import { useAgentStore } from '@/stores';

export default function ToolsPanel() {
  const { toolResults } = useAgentStore();
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');

  // Build tool usage stats from toolResults
  const toolUsageMap = toolResults.reduce<Record<string, number>>((acc, tr) => {
    acc[tr.toolName] = (acc[tr.toolName] || 0) + 1;
    return acc;
  }, {});

  const filteredCategories = TOOL_CATEGORIES
    .filter((cat) => filter === 'all' || cat.id === filter)
    .map((cat) => ({
      ...cat,
      tools: cat.tools.filter(
        (t) =>
          !search ||
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          t.description.toLowerCase().includes(search.toLowerCase())
      ),
    }))
    .filter((cat) => cat.tools.length > 0);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Panel Header */}
      <div className="flex-none px-6 py-4 border-b border-coffee-light">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-primary icon-filled">apps</span>
              Tools Inventory
            </h2>
            <p className="text-xs text-cream-muted/60 mt-0.5">
              {TOOL_COUNT} tools tersedia di {TOOL_CATEGORIES.length} kategori
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Usage stats badge */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/30">
              <span className="material-symbols-outlined text-primary text-sm">bolt</span>
              <span className="text-xs text-primary font-semibold">{toolResults.length} dipakai</span>
            </div>
          </div>
        </div>

        {/* Search + Filter */}
        <div className="flex gap-3">
          {/* Search bar */}
          <div className="flex-1 relative">
            <span className="material-symbols-outlined text-cream-muted/50 absolute left-3 top-1/2 -translate-y-1/2 text-lg">search</span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari tool..."
              className="w-full bg-coffee-medium border-none rounded-lg py-2 pl-10 pr-4 text-sm text-white placeholder:text-cream-muted/40 focus:ring-2 focus:ring-primary focus:outline-none"
            />
          </div>
          {/* Category filter dropdown */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-coffee-medium border-none rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-primary focus:outline-none cursor-pointer"
          >
            <option value="all">Semua Kategori</option>
            {TOOL_CATEGORIES.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name} ({cat.tools.length})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tool Grid */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {filteredCategories.map((category) => (
          <div key={category.id}>
            {/* Category header */}
            <div className="flex items-center gap-2 mb-3">
              <span
                className="material-symbols-outlined text-lg icon-filled"
                style={{ color: category.color }}
              >
                {category.icon}
              </span>
              <h3 className="text-sm font-bold text-white">{category.name}</h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-coffee-medium text-cream-muted">
                {category.tools.length}
              </span>
              {/* Service status for external tools */}

            </div>

            {/* Tool cards grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {category.tools.map((tool) => {
                const usageCount = toolUsageMap[tool.name] || 0;
                return (
                  <div key={tool.name} className="tool-card group">
                    <div className="flex items-start gap-3">
                      {/* Tool icon */}
                      <div
                        className="flex-none w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{ background: `${category.color}15` }}
                      >
                        <span
                          className="material-symbols-outlined text-xl icon-filled"
                          style={{ color: category.color }}
                        >
                          {tool.icon}
                        </span>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-semibold text-white truncate">{tool.name}</h4>
                          {usageCount > 0 && (
                            <span className="flex-none text-[10px] px-1.5 py-0.5 rounded-full bg-primary/20 text-primary font-bold">
                              ×{usageCount}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-cream-muted/60 mt-0.5 line-clamp-2">{tool.description}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {/* No results */}
        {filteredCategories.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <span className="material-symbols-outlined text-4xl text-cream-muted/30 mb-3">search_off</span>
            <p className="text-sm text-cream-muted/60">Tidak ditemukan tool yang cocok</p>
          </div>
        )}
      </div>
    </div>
  );
}
