import numpy as np
from scipy.ndimage import gaussian_filter


def grayscale(image_array):
    red_channel = image_array[..., 0]
    green_channel = image_array[..., 1]
    blue_channel = image_array[..., 2]

    grayscale_image = (red_channel * 0.299 + green_channel * 0.587 + blue_channel * 0.114)
    return grayscale_image.astype(np.uint8)


def gaussian_blur(image_array, sigma=1):
    # Proveravamo da li je grayscale slika (ima samo jedan kanal)
    if len(image_array.shape) == 2:
        # Ako je grayscale, primenjujemo Gaussian blur direktno na nju
        blurred_image = gaussian_filter(image_array, sigma=sigma)
    else:
        # Inače, radimo blur na svaki RGB kanal posebno
        red_channel = image_array[..., 0]
        green_channel = image_array[..., 1]
        blue_channel = image_array[..., 2]

        blurred_red = gaussian_filter(red_channel, sigma=sigma)
        blurred_green = gaussian_filter(green_channel, sigma=sigma)
        blurred_blue = gaussian_filter(blue_channel, sigma=sigma)

        # Kombinujemo kanale nazad u jednu sliku
        blurred_image = np.zeros_like(image_array)
        blurred_image[..., 0] = blurred_red
        blurred_image[..., 1] = blurred_green
        blurred_image[..., 2] = blurred_blue

    return blurred_image


def adjust_brightness(image_array, factor=1.0):
    mean_intensity = np.mean(image_array, axis=(0, 1), keepdims=True)
    image_array = (image_array - mean_intensity) * factor + mean_intensity

    adjusted_image = np.where(image_array < 0, 0, image_array)
    adjusted_image = np.where(adjusted_image > 255, 255, adjusted_image)

    return adjusted_image.astype(np.uint8)