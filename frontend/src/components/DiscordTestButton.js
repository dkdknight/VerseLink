import React, { useState } from 'react';
import { discordService } from '../services/discordService';

const DiscordTestButton = ({ orgId, orgName, testType = 'connection' }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [showResults, setShowResults] = useState(false);

  const testTypeLabels = {
    connection: 'Connexion générale',
    events_channel: 'Canal événements',
    tournaments_channel: 'Canal tournois'
  };

  const handleTest = async () => {
    setIsLoading(true);
    setTestResults(null);
    
    try {
      const results = await discordService.testConnection(orgId, testType);
      setTestResults(results);
      setShowResults(true);
    } catch (error) {
      setTestResults({
        success: false,
        summary: 'Erreur lors du test',
        tests: [{
          name: 'Test de connexion',
          success: false,
          message: error.response?.data?.detail || error.message || 'Erreur inconnue'
        }]
      });
      setShowResults(true);
    } finally {
      setIsLoading(false);
    }
  };

  const getTestIcon = (success) => {
    return success ? '✅' : '❌';
  };

  const getResultColor = (success) => {
    return success ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="discord-test-component">
      <div className="flex items-center space-x-3">
        <button
          onClick={handleTest}
          disabled={isLoading}
          className={`
            px-4 py-2 rounded-lg font-medium transition-all duration-200
            ${isLoading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : testResults?.success 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : testResults?.success === false
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-discord hover:bg-discord-dark text-white'
            }
          `}
        >
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              <span>Test en cours...</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <span>🔧</span>
              <span>Tester {testTypeLabels[testType]}</span>
              {testResults && (
                <span>{testResults.success ? '✅' : '❌'}</span>
              )}
            </div>
          )}
        </button>

        {testResults && (
          <div className={`text-sm font-medium ${getResultColor(testResults.success)}`}>
            {testResults.summary}
          </div>
        )}
      </div>

      {/* Résultats détaillés */}
      {showResults && testResults && (
        <div className="mt-4 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-lg font-semibold text-white">
              Résultats du test - {orgName}
            </h4>
            <button
              onClick={() => setShowResults(false)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className={`text-sm font-medium mb-3 ${getResultColor(testResults.success)}`}>
            {testResults.summary}
          </div>

          <div className="space-y-2">
            {testResults.tests?.map((test, index) => (
              <div key={index} className="flex items-start space-x-3 p-2 bg-gray-700 rounded">
                <span className="text-lg">{getTestIcon(test.success)}</span>
                <div className="flex-1">
                  <div className="font-medium text-white">{test.name}</div>
                  <div className={`text-sm ${getResultColor(test.success)}`}>
                    {test.message}
                  </div>
                  {test.discord_message_link && (
                    <a
                      href={test.discord_message_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-sm underline mt-1 inline-block"
                    >
                      📱 Voir le message de test sur Discord
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>

          {testResults.success && (
            <div className="mt-3 p-3 bg-green-900/20 border border-green-600 rounded">
              <div className="text-green-400 font-medium">🎉 Parfait !</div>
              <div className="text-green-300 text-sm">
                La publication automatique d'événements fonctionnera correctement pour cette organisation.
              </div>
            </div>
          )}

          {!testResults.success && (
            <div className="mt-3 p-3 bg-red-900/20 border border-red-600 rounded">
              <div className="text-red-400 font-medium">⚠️ Action requise</div>
              <div className="text-red-300 text-sm">
                Corrigez les problèmes identifiés pour activer la publication automatique.
                Contactez un administrateur Discord si nécessaire.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DiscordTestButton;