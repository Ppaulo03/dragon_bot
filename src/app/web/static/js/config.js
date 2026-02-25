export const CONFIG = Object.freeze({
    VALIDATION: {
        'send_sticker': '.png, .jpg, .jpeg, .webp',
        'send_image': '.png, .jpg, .jpeg, .gif, .webp',
        'send_audio': '.mp3, .ogg, .wav, .m4a',
        'send_text': '.txt, .json',
        'default': '*'
    },
    SELECTORS: {
        card: '.rule-card',
        triggerContainer: 'container-triggers',
        fallbackContainer: 'container-no-triggers',
        previewModal: '.preview-modal'
    },
    UI: {
        longPressDuration: 500,
        sortableAnimation: 150
    }
});