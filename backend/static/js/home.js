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
        get sentenceSliderMax() {
            return Math.min(20, Math.max(1, this.totalSentences || 1));
        },
        get abstractiveMinBound() {
            return 20;
        },
        get abstractiveMaxBound() {
            return Math.max(60, Math.min(500, Math.floor(this.totalWords * 0.3) || 150));
        },
        get minWordsSliderMax() {
            return Math.max(this.abstractiveMinBound, this.abstractiveMaxBound - 10);
        },
        get maxWordsSliderMin() {
            return Math.min(this.abstractiveMaxBound - 10, this.minWords + 10);
        },
        normalizeSavedModel(model) {
            const allowedModels = [
                'extractive_textrank',
                'extractive_lsa',
                'extractive_lexrank',
                'cointegrated/rut5-base-absum',
                'IlyaGusev/rut5_base_sum_gazeta',
                'Azerotorez/Scientific_paper_rusumm',
                'IlyaGusev/mbart_ru_sum_gazeta'
            ];
            return allowedModels.includes(model) ? model : 'extractive_textrank';
        },
        normalizeExtractiveRange() {
            if (this.sentenceCount > this.sentenceSliderMax) {
                this.sentenceCount = this.sentenceSliderMax;
            }
            if (this.sentenceCount < 1) {
                this.sentenceCount = 1;
            }
        },
        normalizeAbstractiveRange() {
            const minBound = this.abstractiveMinBound;
            const maxBound = this.abstractiveMaxBound;
            let nextMin = this.minWords;
            let nextMax = this.maxWords;

            nextMin = Math.round(nextMin / 10) * 10;
            nextMax = Math.round(nextMax / 10) * 10;

            nextMin = Math.max(minBound, Math.min(nextMin, maxBound - 10));
            nextMax = Math.max(nextMin + 10, Math.min(nextMax, maxBound));

            if (nextMax > maxBound) {
                nextMax = maxBound;
                nextMin = Math.max(minBound, nextMax - 10);
            }

            if (this.minWords !== nextMin) {
                this.minWords = nextMin;
            }
            if (this.maxWords !== nextMax) {
                this.maxWords = nextMax;
            }
        },
        analyzeAndUpdateSliders() {
            if (!this.text.trim()) {
                return;
            }

            if (this.isExtractive) {
                this.normalizeExtractiveRange();
                return;
            }

            this.normalizeAbstractiveRange();
        },
        updateModel() {
            this.analyzeAndUpdateSliders();
            localStorage.setItem('summarizer', JSON.stringify({
                text: this.text,
                model: this.model,
                sentenceCount: this.sentenceCount,
                minWords: this.minWords,
                maxWords: this.maxWords
            }));
        },
        init() {
            const saved = localStorage.getItem('summarizer');
            if (saved) {
                const data = JSON.parse(saved);
                this.text = data.text || '';
                this.model = this.normalizeSavedModel(data.model);
                this.sentenceCount = data.sentenceCount || 5;
                this.minWords = data.minWords || 50;
                this.maxWords = data.maxWords || 150;
            }

            this.analyzeAndUpdateSliders();

            this.$watch('text', () => {
                this.analyzeAndUpdateSliders();
                this.updateModel();
            });
            this.$watch('model', () => this.updateModel());
            this.$watch('sentenceCount', () => this.updateModel());
            this.$watch('minWords', () => {
                this.normalizeAbstractiveRange();
                this.updateModel();
            });
            this.$watch('maxWords', () => {
                this.normalizeAbstractiveRange();
                this.updateModel();
            });

            document.body.addEventListener('homeFileUploaded', event => {
                this.text = event.detail.text || '';
                this.tab = 'text';
                this.updateModel();
                showAlert(`Файл загружен: ${event.detail.filename}`, 'success');
            });
        }
    };
}
