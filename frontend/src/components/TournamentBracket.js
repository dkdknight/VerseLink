import React from 'react';
import { 
  TrophyIcon,
  ChartBarIcon,
  StarIcon
} from '@heroicons/react/24/outline';

const TournamentBracket = ({ tournament, onMatchClick }) => {
  if (!tournament.bracket || !tournament.bracket.rounds) {
    return (
      <div className="text-center py-8">
        <TrophyIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-400">Bracket non disponible</p>
      </div>
    );
  }

  // Round Robin - Show standings
  if (tournament.format === 'rr') {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3 mb-6">
          <ChartBarIcon className="w-6 h-6 text-primary-400" />
          <h3 className="text-xl font-bold text-white">Classement Round Robin</h3>
        </div>
        
        {tournament.bracket.standings && tournament.bracket.standings.length > 0 ? (
          <div className="bg-dark-800 rounded-lg border border-dark-600 overflow-hidden">
            {/* Header */}
            <div className="bg-dark-700 px-4 py-3 border-b border-dark-600">
              <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-300">
                <div className="col-span-1 text-center">#</div>
                <div className="col-span-5">Équipe</div>
                <div className="col-span-2 text-center">V-D</div>
                <div className="col-span-2 text-center">Points</div>
                <div className="col-span-2 text-center">% Victoires</div>
              </div>
            </div>
            
            {/* Standings */}
            <div className="divide-y divide-dark-600">
              {tournament.bracket.standings.map((standing, index) => (
                <div key={standing.team_id} className="px-4 py-3 hover:bg-dark-750 transition-colors duration-200">
                  <div className="grid grid-cols-12 gap-4 items-center">
                    <div className="col-span-1 text-center">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                        index === 0 ? 'bg-accent-gold text-dark-900' :
                        index === 1 ? 'bg-gray-400 text-dark-900' :
                        index === 2 ? 'bg-orange-500 text-white' :
                        'bg-dark-600 text-gray-300'
                      }`}>
                        {standing.position}
                        {index < 3 && (
                          <StarIcon className="w-3 h-3 ml-0.5" />
                        )}
                      </span>
                    </div>
                    
                    <div className="col-span-5">
                      <h4 className="text-white font-medium">{standing.team_name}</h4>
                    </div>
                    
                    <div className="col-span-2 text-center">
                      <span className="text-green-400 font-bold">{standing.wins}</span>
                      <span className="text-gray-400 mx-1">-</span>
                      <span className="text-red-400 font-bold">{standing.losses}</span>
                    </div>
                    
                    <div className="col-span-2 text-center">
                      <span className="text-primary-400 font-bold text-lg">{standing.points}</span>
                    </div>
                    
                    <div className="col-span-2 text-center">
                      <span className="text-gray-300">
                        {(standing.win_percentage * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <ChartBarIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">Aucun classement disponible</p>
          </div>
        )}
      </div>
    );
  }

  // Single/Double Elimination - Show bracket
  const rounds = Object.entries(tournament.bracket.rounds).sort(([a], [b]) => parseInt(a) - parseInt(b));
  
  if (rounds.length === 0) {
    return (
      <div className="text-center py-8">
        <TrophyIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-400">Bracket non généré</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3 mb-6">
        <TrophyIcon className="w-6 h-6 text-primary-400" />
        <h3 className="text-xl font-bold text-white">
          Bracket {tournament.format === 'se' ? 'Simple Élimination' : 'Double Élimination'}
        </h3>
        <div className="text-sm text-gray-400">
          Round {tournament.current_round} / {tournament.rounds_total}
        </div>
      </div>
      
      {/* Bracket Grid */}
      <div className="bracket-container overflow-x-auto">
        <div 
          className="bracket-grid"
          style={{ 
            display: 'grid',
            gridTemplateColumns: `repeat(${rounds.length}, minmax(250px, 1fr))`,
            gap: '2rem',
            minWidth: `${rounds.length * 270}px`,
            padding: '1rem'
          }}
        >
          {rounds.map(([roundNum, matches]) => (
            <div key={roundNum} className="bracket-round">
              {/* Round Header */}
              <div className="text-center mb-6">
                <h4 className="text-lg font-semibold text-primary-400">
                  {getRoundName(parseInt(roundNum), tournament.rounds_total)}
                </h4>
                <div className="text-sm text-gray-400">
                  {matches.length} match{matches.length > 1 ? 's' : ''}
                </div>
              </div>
              
              {/* Matches */}
              <div className="space-y-4">
                {matches.map((match, index) => (
                  <BracketMatch
                    key={match.match_id || index}
                    match={match}
                    onClick={() => onMatchClick && onMatchClick(match)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Tournament Progress */}
      <div className="bg-dark-800 rounded-lg p-4 border border-dark-600">
        <div className="flex items-center justify-between text-sm">
          <div className="text-gray-400">
            Progression du tournoi
          </div>
          <div className="text-primary-400 font-medium">
            {Math.round(
              (tournament.current_round / tournament.rounds_total) * 100
            )}% terminé
          </div>
        </div>
        
        <div className="mt-2 bg-dark-700 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-primary-600 to-primary-400 h-2 rounded-full transition-all duration-300"
            style={{ 
              width: `${(tournament.current_round / tournament.rounds_total) * 100}%` 
            }}
          />
        </div>
      </div>
    </div>
  );
};

const BracketMatch = ({ match, onClick }) => {
  const getStateColor = (state) => {
    switch (state) {
      case 'verified':
        return 'border-green-500/50 bg-green-900/20';
      case 'reported':
        return 'border-yellow-500/50 bg-yellow-900/20';
      case 'live':
        return 'border-blue-500/50 bg-blue-900/20';
      case 'disputed':
        return 'border-red-500/50 bg-red-900/20';
      default:
        return 'border-dark-600 bg-dark-700/50';
    }
  };

  const getStateText = (state) => {
    switch (state) {
      case 'verified': return 'Terminé';
      case 'reported': return 'Reporté';
      case 'live': return 'En cours';
      case 'disputed': return 'Contesté';
      default: return 'À venir';
    }
  };

  return (
    <div 
      className={`
        border-2 rounded-lg p-3 transition-all duration-200 cursor-pointer
        hover:scale-105 hover:shadow-lg
        ${getStateColor(match.state)}
      `}
      onClick={onClick}
    >
      {/* Match State */}
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs px-2 py-1 rounded font-medium ${
          match.state === 'verified' ? 'bg-green-600 text-white' :
          match.state === 'reported' ? 'bg-yellow-600 text-white' :
          match.state === 'live' ? 'bg-blue-600 text-white' :
          match.state === 'disputed' ? 'bg-red-600 text-white' :
          'bg-gray-600 text-gray-300'
        }`}>
          {getStateText(match.state)}
        </span>
        
        {match.round && (
          <span className="text-xs text-gray-400">
            R{match.round}
          </span>
        )}
      </div>
      
      {/* Teams */}
      <div className="space-y-1">
        {/* Team A */}
        <div className={`flex items-center justify-between p-2 rounded ${
          match.winner?.id === match.team_a?.id ? 'bg-green-900/40 text-green-300' : 'text-gray-300'
        }`}>
          <div className="flex items-center space-x-2 flex-1 min-w-0">
            {match.team_a?.seed && (
              <span className="bg-primary-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold flex-shrink-0">
                {match.team_a.seed}
              </span>
            )}
            <span className="font-medium truncate">
              {match.team_a?.name || 'TBD'}
            </span>
          </div>
          
          {match.score_a !== null && (
            <span className={`font-bold text-lg ml-2 ${
              match.winner?.id === match.team_a?.id ? 'text-green-400' : 'text-gray-400'
            }`}>
              {match.score_a}
            </span>
          )}
        </div>
        
        {/* Team B */}
        <div className={`flex items-center justify-between p-2 rounded ${
          match.winner?.id === match.team_b?.id ? 'bg-green-900/40 text-green-300' : 'text-gray-300'
        }`}>
          <div className="flex items-center space-x-2 flex-1 min-w-0">
            {match.team_b?.seed && (
              <span className="bg-primary-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold flex-shrink-0">
                {match.team_b.seed}
              </span>
            )}
            <span className="font-medium truncate">
              {match.team_b?.name || 'TBD'}
            </span>
          </div>
          
          {match.score_b !== null && (
            <span className={`font-bold text-lg ml-2 ${
              match.winner?.id === match.team_b?.id ? 'text-green-400' : 'text-gray-400'
            }`}>
              {match.score_b}
            </span>
          )}
        </div>
      </div>
      
      {/* Winner indicator */}
      {match.winner && (
        <div className="mt-2 text-center">
          <span className="inline-flex items-center text-xs text-green-400 font-medium">
            <TrophyIcon className="w-3 h-3 mr-1" />
            {match.winner.name}
          </span>
        </div>
      )}
    </div>
  );
};

const getRoundName = (roundNum, totalRounds) => {
  if (roundNum === totalRounds) {
    return 'Finale';
  } else if (roundNum === totalRounds - 1) {
    return 'Demi-finale';
  } else if (roundNum === totalRounds - 2) {
    return 'Quart de finale';
  } else if (roundNum === 1) {
    return 'Premier tour';
  } else {
    return `Round ${roundNum}`;
  }
};

export default TournamentBracket;