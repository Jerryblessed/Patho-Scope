document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const fileNameDiv = document.getElementById('file-name');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loader = document.getElementById('loader-overlay');
    const historyList = document.getElementById('history-list');

    const placeholder = document.getElementById('analysis-placeholder');
    const analysisContent = document.getElementById('analysis-content');
    const analyzedImage = document.getElementById('analyzed-image');
    const predictionText = document.getElementById('prediction-text');
    const confidenceText = document.getElementById('confidence-text');
    const aiExplanation = document.getElementById('ai-explanation');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDiv.textContent = fileInput.files[0].name;
            analyzeBtn.disabled = false;
        } else {
            fileNameDiv.textContent = 'No file selected.';
            analyzeBtn.disabled = true;
        }
    });

    const displayAnalysis = (data) => {
        placeholder.style.display = 'none';
        analysisContent.style.display = 'block';

        analyzedImage.src = `data:image/jpeg;base64,${data.image_b64}`;
        predictionText.textContent = data.prediction;
        predictionText.className = `prediction-${data.prediction.split(' ')[0]}`;
        confidenceText.textContent = `${data.confidence}%`;
        aiExplanation.textContent = data.ai_explanation;
    };

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (fileInput.files.length === 0) return;

        loader.style.display = 'flex';
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Analysis failed.');
            }
            const data = await response.json();
            displayAnalysis(data);
            addHistoryItem(data, true);

        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            loader.style.display = 'none';
        }
    });

    const addHistoryItem = (data, isActive = false) => {
        const newItem = document.createElement('li');
        newItem.className = 'history-item';
        if (isActive) {
            document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
            newItem.classList.add('active');
        }
        newItem.dataset.id = data._id;
        newItem.innerHTML = `
            <div class="history-item-info">
                <strong class="prediction-${data.prediction.split(' ')[0]}">${data.prediction}</strong>
                <small>${data.timestamp}</small>
            </div>
            <button class="delete-btn" data-id="${data._id}">×</button>`;
        historyList.prepend(newItem);
    };

    historyList.addEventListener('click', async (e) => {
        const target = e.target;

        if (target.classList.contains('delete-btn')) {
            e.stopPropagation();
            const id = target.dataset.id;
            if (!confirm('Are you sure you want to delete this analysis?')) return;

            try {
                await fetch(`/delete_analysis/${id}`);
                target.closest('.history-item').remove();
                placeholder.style.display = 'flex';
                analysisContent.style.display = 'none';
            } catch (error) {
                alert('Failed to delete history item.');
            }

        } else if (target.closest('.history-item')) {
            const item = target.closest('.history-item');
            const id = item.dataset.id;

            document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');

            loader.style.display = 'flex';
            try {
                const response = await fetch(`/get_analysis/${id}`);
                if (!response.ok) throw new Error('Could not fetch analysis.');
                const data = await response.json();
                displayAnalysis(data);
            } catch (error) {
                alert(error.message);
            } finally {
                loader.style.display = 'none';
            }
        }
    });
});