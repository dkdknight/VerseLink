import React, { useState } from 'react';
import { DocumentDuplicateIcon, CheckIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        toast.success('ID copié !');
        setTimeout(() => setCopied(false), 2000);
        return;
      }
      
      // Fallback for older browsers or non-HTTPS
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      const successful = document.execCommand('copy');
      textArea.remove();
      
      if (successful) {
        setCopied(true);
        toast.success('ID copié !');
        setTimeout(() => setCopied(false), 2000);
      } else {
        throw new Error('Copy command failed');
      }
    } catch (err) {
      console.error('Copy failed:', err);
      toast.error("Impossible de copier l'ID");
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="btn-ghost flex items-center text-sm"
    >
      {copied ? (
        <>
          <CheckIcon className="w-4 h-4 mr-1" />
          Copié !
        </>
      ) : (
        <>
          <DocumentDuplicateIcon className="w-4 h-4 mr-1" />
          Copier
        </>
      )}
    </button>
  );
};

export default CopyButton;