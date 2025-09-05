import React, { useState } from 'react';
import { 
  XMarkIcon,
  DocumentArrowUpIcon,
  TrophyIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { tournamentService } from '../services/tournamentService';

const MatchReportModal = ({ isOpen, onClose, match, currentUser, onMatchUpdated }) => {
  const [scoreA, setScoreA] = useState('');
  const [scoreB, setScoreB] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const scoreANum = parseInt(scoreA);
    const scoreBNum = parseInt(scoreB);
    
    if (isNaN(scoreANum) || isNaN(scoreBNum) || scoreANum < 0 || scoreBNum < 0) {
      toast.error('Les scores doivent être des nombres positifs');
      return;
    }
    
    if (scoreANum === scoreBNum) {
      toast.error('Les scores ne peuvent pas être égaux - il doit y avoir un gagnant');
      return;
    }

    try {
      setSubmitting(true);
      await tournamentService.reportMatchScore(match.id, {
        score_a: scoreANum,
        score_b: scoreBNum,
        notes: notes.trim() || null
      });
      
      toast.success('Score reporté avec succès !');
      
      // Upload attachments if any
      if (selectedFiles.length > 0) {
        await uploadAttachments();
      }
      
      onMatchUpdated();
      onClose();
      
      // Reset form
      resetForm();
    } catch (error) {
      console.error('Failed to report score:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors du report du score');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const uploadAttachments = async () => {
    setUploading(true);
    let successCount = 0;
    
    for (const file of selectedFiles) {
      try {
        await tournamentService.uploadMatchAttachment(match.id, file.file, file.description);
        successCount++;
      } catch (error) {
        console.error('Failed to upload attachment:', error);
        toast.error(`Erreur lors de l'upload de ${file.file.name}`);
      }
    }
    
    if (successCount > 0) {
      toast.success(`${successCount} fichier(s) uploadé(s) avec succès`);
    }
    
    setUploading(false);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const newFiles = files.map(file => ({
      file,
      description: '',
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    }));
    
    setSelectedFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => {
      const file = prev[index];
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter((_, i) => i !== index);
    });
  };

  const updateFileDescription = (index, description) => {
    setSelectedFiles(prev => 
      prev.map((file, i) => 
        i === index ? { ...file, description } : file
      )
    );
  };

  const resetForm = () => {
    setScoreA('');
    setScoreB('');
    setNotes('');
    setSelectedFiles([]);
  };

  const canReport = () => {
    if (!currentUser || !match) return false;
    
    // Check if user is captain of one of the teams
    return match.can_report || 
           (match.team_a_id && match.team_a_captain_id === currentUser.id) ||
           (match.team_b_id && match.team_b_captain_id === currentUser.id);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-dark-600">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-600">
          <div className="flex items-center space-x-3">
            <TrophyIcon className="w-6 h-6 text-primary-400" />
            <h2 className="text-xl font-semibold text-white">Reporter le score</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Match Info */}
          <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-xs bg-primary-600 text-white px-2 py-1 rounded">
                Round {match.round}
              </span>
              <ClockIcon className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">
                {match.scheduled_at && new Date(match.scheduled_at).toLocaleDateString('fr-FR')}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <h4 className="text-white font-medium">{match.team_a_name || 'TBD'}</h4>
                <p className="text-sm text-gray-400">Équipe A</p>
              </div>
              <div className="text-center">
                <h4 className="text-white font-medium">{match.team_b_name || 'TBD'}</h4>
                <p className="text-sm text-gray-400">Équipe B</p>
              </div>
            </div>
          </div>

          {/* Score Input */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Score {match.team_a_name || 'Équipe A'} *
              </label>
              <input
                type="number"
                value={scoreA}
                onChange={(e) => setScoreA(e.target.value)}
                className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-center text-lg font-bold focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
                required
                min="0"
                max="999"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Score {match.team_b_name || 'Équipe B'} *
              </label>
              <input
                type="number"
                value={scoreB}
                onChange={(e) => setScoreB(e.target.value)}
                className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-center text-lg font-bold focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
                required
                min="0"
                max="999"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notes (optionnel)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Commentaires sur le match, stratégies utilisées, moments marquants..."
              rows={3}
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              maxLength={500}
            />
            <p className="text-xs text-gray-400 mt-1">
              {notes.length}/500 caractères
            </p>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Pièces jointes (screenshots, vidéos)
            </label>
            
            <div className="space-y-4">
              {/* File Input */}
              <div>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  accept="image/*,video/*,.txt,.json,.csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <label
                  htmlFor="file-upload"
                  className="inline-flex items-center px-4 py-2 border border-dashed border-dark-600 rounded-lg text-gray-300 hover:text-white hover:border-primary-500 cursor-pointer transition-colors duration-200"
                >
                  <DocumentArrowUpIcon className="w-5 h-5 mr-2" />
                  Ajouter des fichiers
                </label>
                <p className="text-xs text-gray-400 mt-1">
                  Images, vidéos, logs (max 50MB par fichier)
                </p>
              </div>

              {/* Selected Files */}
              {selectedFiles.length > 0 && (
                <div className="space-y-2">
                  {selectedFiles.map((fileData, index) => (
                    <div key={index} className="bg-dark-700 rounded-lg p-3 border border-dark-600">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            {fileData.preview && (
                              <img
                                src={fileData.preview}
                                alt="Preview"
                                className="w-10 h-10 object-cover rounded"
                              />
                            )}
                            <div>
                              <p className="text-white text-sm font-medium">
                                {fileData.file.name}
                              </p>
                              <p className="text-gray-400 text-xs">
                                {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                              </p>
                            </div>
                          </div>
                          
                          <input
                            type="text"
                            placeholder="Description (optionnel)"
                            value={fileData.description}
                            onChange={(e) => updateFileDescription(index, e.target.value)}
                            className="w-full px-2 py-1 bg-dark-800 border border-dark-600 rounded text-white text-sm focus:ring-1 focus:ring-primary-500 focus:border-transparent"
                            maxLength={200}
                          />
                        </div>
                        
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="ml-2 p-1 text-gray-400 hover:text-red-400 transition-colors duration-200"
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Warning */}
          {!canReport() && (
            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
              <p className="text-yellow-300 text-sm">
                ⚠️ Seuls les capitaines d'équipe peuvent reporter les scores.
              </p>
            </div>
          )}

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-dark-600">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-300 hover:text-white transition-colors duration-200"
              disabled={submitting || uploading}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={submitting || uploading || !canReport() || !scoreA || !scoreB}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center"
            >
              {submitting ? (
                <>
                  <div className="loading-spinner w-4 h-4 mr-2"></div>
                  Envoi...
                </>
              ) : (
                <>
                  <TrophyIcon className="w-4 h-4 mr-2" />
                  Reporter le score
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MatchReportModal;