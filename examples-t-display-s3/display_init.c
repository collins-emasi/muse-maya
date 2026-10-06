/*
 * T-Display-S3 Display Initialization Example
 * 
 * This example shows how to initialize the ST7789 display controller
 * on the LilyGO T-Display-S3 board for use with the Muse Gadget SDK.
 */

#include <stdio.h>
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"

// Display GPIO pins for T-Display-S3
#define LCD_GPIO_MOSI  3
#define LCD_GPIO_CLK   6
#define LCD_GPIO_CS    10
#define LCD_GPIO_DC    8
#define LCD_GPIO_RST   9
#define LCD_GPIO_BL    38

#define SPI_HOST       SPI2_HOST
#define SPI_CLOCK_FREQ 40000000  // 40 MHz

static const char *TAG = "LCD_INIT";
static spi_device_handle_t spi_handle;

/**
 * Write SPI command byte
 */
static void lcd_write_cmd(uint8_t cmd) {
    esp_err_t ret;
    spi_transaction_t t = {
        .length = 8,
        .tx_buffer = &cmd,
        .user = (void *)0,  // DC pin low for command
    };
    
    gpio_set_level(LCD_GPIO_DC, 0);
    ret = spi_device_transmit(spi_handle, &t);
    assert(ret == ESP_OK);
}

/**
 * Write SPI data byte
 */
static void lcd_write_data(uint8_t data) {
    esp_err_t ret;
    spi_transaction_t t = {
        .length = 8,
        .tx_buffer = &data,
        .user = (void *)1,  // DC pin high for data
    };
    
    gpio_set_level(LCD_GPIO_DC, 1);
    ret = spi_device_transmit(spi_handle, &t);
    assert(ret == ESP_OK);
}

/**
 * Initialize the ST7789 display controller
 */
static void lcd_init(void) {
    ESP_LOGI(TAG, "Initializing ST7789 display...");
    
    // Reset sequence
    gpio_set_level(LCD_GPIO_RST, 0);
    vTaskDelay(100 / portTICK_PERIOD_MS);
    gpio_set_level(LCD_GPIO_RST, 1);
    vTaskDelay(100 / portTICK_PERIOD_MS);
    
    // Basic initialization commands for ST7789
    lcd_write_cmd(0x01);  // Software reset
    vTaskDelay(50 / portTICK_PERIOD_MS);
    
    lcd_write_cmd(0x11);  // Sleep out
    vTaskDelay(120 / portTICK_PERIOD_MS);
    
    lcd_write_cmd(0x36);  // MADCTL (memory access control)
    lcd_write_data(0x00);
    
    lcd_write_cmd(0x3A);  // COLMOD (interface pixel format)
    lcd_write_data(0x05); // 16-bit color
    
    lcd_write_cmd(0x21);  // INVON (display inversion on)
    
    lcd_write_cmd(0x29);  // DISPON (display on)
    vTaskDelay(50 / portTICK_PERIOD_MS);
    
    // Enable backlight
    gpio_set_level(LCD_GPIO_BL, 1);
    
    ESP_LOGI(TAG, "Display initialized successfully!");
}

/**
 * Configure GPIO pins for display control
 */
static void gpio_init(void) {
    gpio_config_t io_conf = {
        .mode = GPIO_MODE_OUTPUT,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    
    // Configure control pins
    io_conf.pin_bit_mask = (1ULL << LCD_GPIO_DC) | 
                           (1ULL << LCD_GPIO_RST) | 
                           (1ULL << LCD_GPIO_BL);
    gpio_config(&io_conf);
    
    // Set initial levels
    gpio_set_level(LCD_GPIO_DC, 0);
    gpio_set_level(LCD_GPIO_RST, 1);
    gpio_set_level(LCD_GPIO_BL, 0);  // Backlight off initially
}

/**
 * Configure SPI bus for display communication
 */
static void spi_init(void) {
    ESP_LOGI(TAG, "Initializing SPI bus...");
    
    spi_bus_config_t buscfg = {
        .mosi_io_num = LCD_GPIO_MOSI,
        .miso_io_num = -1,  // No MISO needed for display
        .sclk_io_num = LCD_GPIO_CLK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 32000,
    };
    
    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = SPI_CLOCK_FREQ,
        .mode = 0,  // SPI mode 0
        .spics_io_num = LCD_GPIO_CS,
        .queue_size = 7,
    };
    
    ESP_ERROR_CHECK(spi_bus_initialize(SPI_HOST, &buscfg, SPI_DMA_CH_AUTO));
    ESP_ERROR_CHECK(spi_bus_add_device(SPI_HOST, &devcfg, &spi_handle));
    
    ESP_LOGI(TAG, "SPI bus initialized");
}

/**
 * Application entry point
 */
void app_main(void) {
    ESP_LOGI(TAG, "T-Display-S3 Display Initialization Example");
    
    // Initialize GPIO pins
    gpio_init();
    
    // Initialize SPI bus
    spi_init();
    
    // Initialize LCD display
    lcd_init();
    
    ESP_LOGI(TAG, "Display ready for use!");
    ESP_LOGI(TAG, "Resolution: 320×170 pixels");
    ESP_LOGI(TAG, "Color mode: 16-bit RGB565");
}
