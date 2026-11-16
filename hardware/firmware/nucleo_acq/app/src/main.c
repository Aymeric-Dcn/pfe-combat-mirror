/*
 * main.c
 *
 *  Created on: Feb 26, 2025
 *      Author: User
 */


#include "stm32f0xx.h"
#include "bsp.h"
#include "main.h"
#include "frame.h"


// Static functions
static void SystemClock_Config (void);

// Global variables
uint8_t		timebase_irq = 0;
uint16_t	adc_dma_buffer[2*ADC_NB_CHANNELS];

/*
 * Force plate acquisition
 * TIM3 triggers an ADC scan every 500us (2kHz): 4 FlexiForce channels,
 * V_REF and VREFINT. The DMA interrupt queues each scan as a frame
 * (frame.c), and the main loop sends the frames to the PC.
 * Started from the 3.5-adc-dma tutorial (multi-channel ADC with DMA).
 */

int main()
{
	// Configure System Clock
	SystemClock_Config();

	// Initialize LED
	BSP_LED_Init();

	// Initialize Console (921600 bauds, TX by DMA)
	BSP_Console_Init();

	// Initialize 500ms timebase for the LED
	BSP_TIMER_Timebase_Init();

	// Initialize ADC with DMA, then start the 2kHz trigger
	BSP_ADC_Init();
	BSP_TIMER_Trigger_Init();

	BSP_NVIC_Init();

	// Main loop
	while(1)
	{
		// Send the queued frames
		FRAME_Send();

		// Do every 500ms
		if(timebase_irq == 1)
		{
			// Heartbeat
			BSP_LED_Toggle();

			// Reset timebase flag
			timebase_irq = 0;
		}
	}
}

/*
 * Clock configuration for the Nucleo STM32F072RB board
 * HSE input Bypass Mode            -> 8MHz
 * SYSCLK, AHB, APB1                -> 48MHz
 */

static void SystemClock_Config()
{
	uint32_t	HSE_Status;
	uint32_t	PLL_Status;
	uint32_t	SW_Status;
	uint32_t	timeout = 0;
	timeout = 1000000;

	// Start HSE in Bypass Mode
	RCC->CR |= RCC_CR_HSEBYP;
	RCC->CR |= RCC_CR_HSEON;

	// Wait until HSE is ready
	do
	{
		HSE_Status = RCC->CR & RCC_CR_HSERDY_Msk;
		timeout--;
	} while ((HSE_Status == 0) && (timeout > 0));

	// Select HSE as PLL input source
	RCC->CFGR &= ~RCC_CFGR_PLLSRC_Msk;
	RCC->CFGR |= (0x02 <<RCC_CFGR_PLLSRC_Pos);

	// Set PLL PREDIV to /1
	RCC->CFGR2 = 0x00000000;

	// Set PLL MUL to x6
	RCC->CFGR &= ~RCC_CFGR_PLLMUL_Msk;
	RCC->CFGR |= (0x04 <<RCC_CFGR_PLLMUL_Pos);

	// Enable the main PLL
	RCC->CR |= RCC_CR_PLLON;
	// Wait until PLL is ready
	do
	{
		PLL_Status = RCC->CR & RCC_CR_PLLRDY_Msk;
		timeout--;
	} while ((PLL_Status == 0) && (timeout > 0));

	// Set AHB prescaler to /1
	RCC->CFGR &= ~RCC_CFGR_HPRE_Msk;
	RCC->CFGR |= RCC_CFGR_HPRE_DIV1;

	//Set APB1 prescaler to /1
	RCC->CFGR &= ~RCC_CFGR_PPRE_Msk;
	RCC->CFGR |= RCC_CFGR_PPRE_DIV1;

	// Enable FLASH Prefetch Buffer and set Flash Latency
	FLASH->ACR = FLASH_ACR_PRFTBE | FLASH_ACR_LATENCY;

	// Select the main PLL as system clock source
	RCC->CFGR &= ~RCC_CFGR_SW;
	RCC->CFGR |= RCC_CFGR_SW_PLL;

	// Wait until PLL becomes main switch input
	do
	{
		SW_Status = (RCC->CFGR & RCC_CFGR_SWS_Msk);
		timeout--;
	} while ((SW_Status != RCC_CFGR_SWS_PLL) && (timeout > 0));

	// Update SystemCoreClock global variable
	SystemCoreClockUpdate();
}
