import io

# import pygame
# from pygame.locals import *


def show_captcha(canvas, captcha_img):
    image = pygame.image.load(io.BytesIO(captcha_img)).convert()
    image = pygame.transform.scale(image, (465, 105))
    canvas.MAIN_SURFACE.fill(canvas.COLORS["BLACK"])
    canvas.MAIN_SURFACE.blit(image, (10, 10))


def gui_with_text_entry(canvas, captcha_img):
    numpad = (
        K_KP0,
        K_KP1,
        K_KP2,
        K_KP3,
        K_KP4,
        K_KP5,
        K_KP6,
        K_KP7,
        K_KP8,
        K_KP9,
    )

    # open pygame window with zoomed captcha image
    show_captcha(canvas, captcha_img)

    # define surface where manual input will be written
    TEXTBOX = pygame.Surface((80, 120))
    chars, col = [], 0
    while True:
        # pygame capture screen update
        charsx = f"{''.join(chars):<6}"
        for colx in range(6):
            text = canvas.FONTS["NUN80B"].render(
                charsx[colx],
                True,
                canvas.COLORS["BLACK"],
                canvas.COLORS["WHITE"],
            )
            TEXTBOX.fill(canvas.COLORS["WHITE"])
            TEXTBOX.blit(text, (12, 5))
            canvas.MAIN_SURFACE.blit(
                TEXTBOX,
                (colx * 90 + 10 + 20 + 500, 10),
            )
        pygame.display.flip()

        # capture keystrokes and add to manual captcha input
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT or (event.type == KEYDOWN and event.key == 27):
                quit()
            elif event.type == KEYDOWN:
                if event.key == K_BACKSPACE:
                    if col == 0:
                        continue
                    chars = chars[:-1]
                    col -= 1
                elif event.key in (K_SPACE, K_RETURN):
                    continue
                elif event.key in numpad:
                    chars.append(str(numpad.index(event.key)))
                    col += 1
                else:
                    try:
                        chars.append(chr(event.key))
                        col += 1
                    except Exception:
                        pass

        # if all chars are complete, return manual captcha as string
        if col == 6:
            canvas.MAIN_SURFACE.fill(canvas.COLORS["GREEN"])
            pygame.display.flip()
            return "".join(chars)
