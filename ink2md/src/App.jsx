/**
 * Main Application Component
 * 
 * @author Sarah Wolff
 * @version 0.5 beta
 * @description Clean router setup with context providers for tabbed interface
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Context Providers
import { AppStateProvider } from './contexts/AppStateContext';
import { ConversionProvider } from './contexts/ConversionContext';
import { HistoryProvider } from './contexts/HistoryContext';
import { SettingsProvider } from './contexts/SettingsContext';

// Components
import TabContainer from './components/common/TabContainer';
import ConverterTab from './components/converter/ConverterTab';
import HistoryTab from './components/history/HistoryTab';
import PromptsTab from './components/prompts/PromptsTab';
import SettingsTab from './components/settings/SettingsTab';

// Styles
import './App.css';

/**
 * Main App component with router and context providers
 * Provides clean separation of concerns with tabbed navigation
 */
function App() {
  return (
    <BrowserRouter>
      <AppStateProvider>
        <ConversionProvider>
          <HistoryProvider>
            <SettingsProvider>
              <div className="app">
                <Routes>
                  <Route path="/" element={<TabContainer />}>
                    {/* Default redirect to converter */}
                    <Route index element={<Navigate to="/converter" replace />} />
                    
                    {/* Tab Routes */}
                    <Route path="converter" element={<ConverterTab />} />
                    <Route path="history" element={<HistoryTab />} />
                    <Route path="prompts" element={<PromptsTab />} />
                    <Route path="settings" element={<SettingsTab />} />
                    
                    {/* Catch-all redirect */}
                    <Route path="*" element={<Navigate to="/converter" replace />} />
                  </Route>
                </Routes>
              </div>
            </SettingsProvider>
          </HistoryProvider>
        </ConversionProvider>
      </AppStateProvider>
    </BrowserRouter>
  );
}

export default App;
