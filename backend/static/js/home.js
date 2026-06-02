function summarizerApp() {
    return {
        tab: 'text',
        text: '',
        model: 'extractive_textrank',
        sentenceCount: 5,
        minWords: 50,
        maxWords: 150,
        loading: false,
        get isExtractive() {
            return this.model.startsWith('extractive');
        },
        get totalSentences() {
            return countSentences(this.text);
        },
        get totalWords() {
            return countWords(this.text);
        },
        get maxSentencesAvailable() {
            return Math.min(20, Math.max(1, this.totalSentences));
        },
        get recommendedMin() {
            return Math.max(20, Math.floor(this.totalWords * 0.05));
        },
        get recommendedMax() {
            return Math.min(500, Math.floor(this.totalWords * 0.3));
        },
        analyzeAndUpdateSliders() {
            const text = this.text.trim();
            if (!text) {
                return;
            }
            if (this.isExtractive) {
                const maxVal = this.maxSentencesAvailable;
                if (this.sentenceCount > maxVal) {
                    this.sentenceCount = maxVal;
                }
                this.$nextTick(() => {
                    if (this.$refs.sentenceSlider) {
                        this.$refs.sentenceSlider.max = maxVal;
                    }
                });
            } else {
                const recMin = this.recommendedMin;
                const recMax = this.recommendedMax;
                if (this.minWords < recMin) {
                    this.minWords = recMin;
                }
                if (this.maxWords > recMax) {
                    this.maxWords = recMax;
                }
                if (this.minWords >= this.maxWords) {
                    this.minWords = recMin;
                    this.maxWords = recMax;
                }
                this.$nextTick(() => {
                    if (this.$refs.minWordsSlider) {
                        this.$refs.minWordsSlider.max = recMax - 10;
                    }
                    if (this.$refs.maxWordsSlider) {
                        this.$refs.maxWordsSlider.min = recMin + 10;
                        this.$refs.maxWordsSlider.max = recMax;
                    }
                });
            }
        },
        updateModel() {
            localStorage.setItem('summarizer', JSON.stringify({
                text: this.text,
                model: this.model,
                sentenceCount: this.sentenceCount,
                minWords: this.minWords,
                maxWords: this.maxWords
            }));
            if (this.text.trim()) {
                this.analyzeAndUpdateSliders();
            }
        },
        init() {
            const saved = localStorage.getItem('summarizer');
            if (saved) {
                const data = JSON.parse(saved);
                this.text = data.text || '';
                this.model = data.model || 'extractive_textrank';
                this.sentenceCount = data.sentenceCount || 5;
                this.minWords = data.minWords || 50;
                this.maxWords = data.maxWords || 150;
            }
            if (this.text.trim()) {
                this.$nextTick(() => this.analyzeAndUpdateSliders());
            }
            this.$watch('text', () => this.analyzeAndUpdateSliders());
            this.$watch('model', () => this.updateModel());
            document.body.addEventListener('homeFileUploaded', (event) => {
                this.text = event.detail.text || '';
                this.tab = 'text';
                this.updateModel();
                showAlert(`Файл загружен: ${event.detail.filename}`, 'success');
            });
        }
    };
}
