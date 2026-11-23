/*
 * bsp.c
 *
 *  Created on: Feb 28, 2025
 *      Author: User
 */

#include "bsp.h"

/*
 * BSP_LED_Init()
 * Initialize LED pin (PA5) as a High-Speed Push-Pull output
 * Set LED initial state to OFF
 */

void BSP_LED_Init()
{
	// Enable GPIOA clock
	RCC->AHBENR |= RCC_AHBENR_GPIOAEN;

	// Configure PA5 as output
	GPIOA->MODER &= ~GPIO_MODER_MODER5_Msk;
	GPIOA->MODER |= (0x01 <<GPIO_MODER_MODER5_Pos);

	// Configure PA5 as a push-pull output
	GPIOA->OTYPER &= ~GPIO_OTYPER_OT_5;

	// Configure PA5 as High-Speed Output
	GPIOA->OSPEEDR &= ~GPIO_OSPEEDR_OSPEEDR5_Msk;
	GPIOA->OSPEEDR |= (0x03 <<GPIO_OSPEEDR_OSPEEDR5_Pos);

	// Disable PA5 Pull-up/PUll-down
	GPIOA->PUPDR &= ~GPIO_PUPDR_PUPDR5_Msk;

	// Set Initial State OFF
	GPIOA->BSRR |= GPIO_BSRR_BR_5;
}


/*
 * BSP_LED_On()
 * Turn ON LED on PA5
 */

void BSP_LED_On()
{
	GPIOA->BSRR = GPIO_BSRR_BS_5;
}

/*
 * BSP_LED_Off()
 * Turn OFF LED on PA5
 */

void BSP_LED_Off()
{
	GPIOA->BSRR = GPIO_BSRR_BR_5;
}

/*
 * BSP_LED_Toggle()
 * Toggle LED on PA5
 */

void BSP_LED_Toggle()
{
	GPIOA->ODR ^= GPIO_ODR_5;
}

/*
 * BSP_PB_Init()
 * Initialize Push-Button pin (PC13) as input without Pull-up/Pull-down
 * Enable EXTI13 on falling edge
 */

void BSP_PB_Init()
{
	// Enable GPIOC clock
	RCC->AHBENR |= RCC_AHBENR_GPIOCEN;

	// Configure PC13 as input
	GPIOC->MODER &= ~GPIO_MODER_MODER13_Msk;
	GPIOC->MODER |= (0x00 <<GPIO_MODER_MODER13_Pos);

	// Disable PC13 Pull-up/Pull-down
	GPIOC->PUPDR &= ~GPIO_PUPDR_PUPDR13_Msk;

	// Enable SYSCFG clock
	RCC->APB2ENR |= RCC_APB2ENR_SYSCFGEN;

	// Select Port C as interrupt source for EXTI line 13
	SYSCFG->EXTICR[3] &= ~ SYSCFG_EXTICR4_EXTI13_Msk;
	SYSCFG->EXTICR[3] |=   SYSCFG_EXTICR4_EXTI13_PC;

	// Enable EXTI line 13
	EXTI->IMR |= EXTI_IMR_IM13;

	// Disable Rising / Enable Falling trigger
	EXTI->RTSR &= ~EXTI_RTSR_RT13;
	EXTI->FTSR |=  EXTI_FTSR_FT13;
}

/*
 * BSP_PB_GetState()
 * Returns the state of the button (0=released, 1=pressed)
 */

uint8_t BSP_PB_GetState()
{
	uint8_t state;
	if ((GPIOC->IDR & GPIO_IDR_13) == GPIO_IDR_13)
	{
		state = 0;
	}
	else
	{
		state = 1;
	}
	return state;
}

/*
 * BSP_Console_Init()
 * USART2 @ 921600 Full Duplex, data link to the PC (ST-LINK virtual COM port)
 * 1 start - 8-bit - 1 stop
 * TX -> PA2 (AF1), sent by DMA1 Channel 4
 * RX -> PA3 (AF1)
 */

void BSP_Console_Init()
{
	// Enable GPIOA clock
	RCC->AHBENR |= RCC_AHBENR_GPIOAEN;
	// Configure PA2 and PA3 as Alternate function
	GPIOA->MODER &= ~(GPIO_MODER_MODER2_Msk | GPIO_MODER_MODER3_Msk);
	GPIOA->MODER |=  (0x02 <<GPIO_MODER_MODER2_Pos) | (0x02 <<GPIO_MODER_MODER3_Pos);
	// Set PA2 and PA3 to AF1 (USART2)
	GPIOA->AFR[0] &= ~(0x0000FF00);
	GPIOA->AFR[0] |=  (0x00001100);
	// Enable USART2 clock
	RCC -> APB1ENR |= RCC_APB1ENR_USART2EN;
	// Clear USART2 configuration (reset state)
	// 8-bit, 1 start, 1 stop, CTS/RTS disabled
	USART2->CR1 = 0x00000000;
	USART2->CR2 = 0x00000000;
	USART2->CR3 = 0x00000000;
	// Select PCLK (APB1) as clock source
	// PCLK -> 48 MHz
	RCC->CFGR3 &= ~RCC_CFGR3_USART2SW_Msk;
	// Baud Rate = 921600
	// With OVER8=1 and Fck=48MHz, USARTDIV = 2*48E6/921600 = 104.1667
	// USARTDIV = 104 -> Actual BaudRate = 923077 -> 0.16% error
	// With OVER8=1, BRR[2:0] = USARTDIV[3:0] >> 1 and BRR[3] must be kept cleared
	USART2->CR1 |= USART_CR1_OVER8;
	USART2->BRR = (104 & 0xFFF0) | ((104 & 0x000F) >> 1);
	// Enable both Transmitter and Receiver
	USART2->CR1 |= USART_CR1_TE | USART_CR1_RE;

	// Setup TX on DMA Channel 4
	// Start DMA clock
	RCC->AHBENR |= RCC_AHBENR_DMA1EN;
	// Reset DMA1 Channel 4 configuration
	DMA1_Channel4->CCR = 0x00000000;
	// Set direction Memory -> Peripheral
	DMA1_Channel4->CCR |= DMA_CCR_DIR;
	// Peripheral is USART2 TDR
	DMA1_Channel4->CPAR = (uint32_t)&USART2->TDR;
	// Peripheral and memory data size are 8-bit (byte)
	DMA1_Channel4->CCR |= (0x00 <<DMA_CCR_PSIZE_Pos) | (0x00 <<DMA_CCR_MSIZE_Pos);
	// Enable auto-increment Memory address
	DMA1_Channel4->CCR |= DMA_CCR_MINC;
	// Memory address and size are set for each transfer (BSP_Console_SendDMA)

	// Enable USART2 DMA Request on TX
	USART2->CR3 |= USART_CR3_DMAT;
	// Enable USART2
	USART2->CR1 |= USART_CR1_UE;
}

/*
 * BSP_Console_SendDMA()
 * Start the DMA transfer of nbytes from buffer to USART2
 * Returns 1 if started, 0 if the previous transfer is not over
 */

uint8_t BSP_Console_SendDMA(uint8_t *buffer, uint16_t nbytes)
{
	// A transfer is in progress if the channel is enabled and not complete
	if (((DMA1_Channel4->CCR & DMA_CCR_EN) == DMA_CCR_EN) && ((DMA1->ISR & DMA_ISR_TCIF4) == 0))
	{
		return 0;
	}

	// Disable channel and clear the transfer complete flag
	DMA1_Channel4->CCR &= ~DMA_CCR_EN;
	DMA1->IFCR = DMA_IFCR_CTCIF4;

	// Set memory address and size, then start
	DMA1_Channel4->CMAR = (uint32_t)buffer;
	DMA1_Channel4->CNDTR = nbytes;
	DMA1_Channel4->CCR |= DMA_CCR_EN;

	return 1;
}

/*
 * BSP_ADC_Init()
 * Initialize ADC for 6 channels conversion with DMA, triggered by TIM3
 * - Channel 0  -> pin PA0 (A0, sensor 1)
 * - Channel 1  -> pin PA1 (A1, sensor 2)
 * - Channel 4  -> pin PA4 (A2, sensor 3)
 * - Channel 8  -> pin PB0 (A3, sensor 4)
 * - Channel 11 -> pin PC1 (A4, V_REF of the conditioning board)
 * - Channel 17 -> internal voltage reference (VREFINT, to measure VDDA)
 * One scan per TIM3 update event. The DMA buffer holds 2 scans:
 * Half Transfer -> first scan ready, Transfer Complete -> second scan ready
 */

extern uint16_t	adc_dma_buffer[2*ADC_NB_CHANNELS];

void BSP_ADC_Init()
{
	// Enable GPIOA, GPIOB and GPIOC clocks
	RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN | RCC_AHBENR_GPIOCEN;

	// Configure pins PA0, PA1, PA4, PB0 and PC1 as analog
	GPIOA->MODER &= ~(GPIO_MODER_MODER0_Msk | GPIO_MODER_MODER1_Msk | GPIO_MODER_MODER4_Msk);
	GPIOA->MODER |=	(0x03 <<GPIO_MODER_MODER0_Pos) | (0x03 <<GPIO_MODER_MODER1_Pos) | (0x03 <<GPIO_MODER_MODER4_Pos);
	GPIOB->MODER &= ~GPIO_MODER_MODER0_Msk;
	GPIOB->MODER |=	(0x03 <<GPIO_MODER_MODER0_Pos);
	GPIOC->MODER &= ~GPIO_MODER_MODER1_Msk;
	GPIOC->MODER |=	(0x03 <<GPIO_MODER_MODER1_Pos);

	// Enable ADC clock
	RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;

	// Reset ADC configuration
	ADC1->CR 	= 0x00000000;
	ADC1->CFGR1  = 0x00000000;
	ADC1->CFGR2  = 0x00000000;
	ADC1->CHSELR = 0x00000000;

	// 12-bit resolution, single conversion mode (one scan per trigger)
	ADC1->CFGR1 |= (0x00 <<ADC_CFGR1_RES_Pos);

	// Select PCLK/4 as ADC clock -> 12MHz (14MHz max)
	ADC1->CFGR2 |= (0x02 <<ADC_CFGR2_CKMODE_Pos);

	// Set sampling time to 71.5 ADC clock cycles
	// (71.5 + 12.5) / 12MHz = 7us per channel, 42us per scan
	// VREFINT needs at least 4us of sampling time
	ADC1->SMPR = 0x06;

	// Select channel 0, 1, 4, 8, 11, 17 (converted in this order)
	ADC1->CHSELR |= ADC_CHSELR_CHSEL0 | ADC_CHSELR_CHSEL1 | ADC_CHSELR_CHSEL4
	             |  ADC_CHSELR_CHSEL8 | ADC_CHSELR_CHSEL11 | ADC_CHSELR_CHSEL17;

	// Enable the internal voltage reference
	ADC->CCR |= ADC_CCR_VREFEN;

	// External trigger on TIM3_TRGO (EXTSEL = 011), rising edge
	ADC1->CFGR1 |= (0x03 <<ADC_CFGR1_EXTSEL_Pos) | (0x01 <<ADC_CFGR1_EXTEN_Pos);

	// Calibrate the ADC (ADC must be disabled)
	ADC1->CR |= ADC_CR_ADCAL;
	while ((ADC1->CR & ADC_CR_ADCAL) == ADC_CR_ADCAL);

	// Start DMA clock
	RCC->AHBENR |= RCC_AHBENR_DMA1EN;

	// Reset DMA1 Channel 1 configuration
	DMA1_Channel1->CCR = 0x00000000;

	// Configure DMA1 Channel 1
	// Peripheral -> Memory
	// Peripheral is 16-bit, no increment
	// Memory is 16-bit, increment
	// Circular mode

	DMA1_Channel1->CCR |= (0x01 <<DMA_CCR_PSIZE_Pos) | (0x01 <<DMA_CCR_MSIZE_Pos) | DMA_CCR_MINC | DMA_CCR_CIRC;

	// Peripheral is ADC1 DR
	DMA1_Channel1->CPAR = (uint32_t)&ADC1->DR;

	// Memory is adc_dma_buffer
	DMA1_Channel1->CMAR = (uint32_t)adc_dma_buffer;

	// Set Memory Buffer size (2 scans)
	DMA1_Channel1->CNDTR = 2*ADC_NB_CHANNELS;

	// Enable DMA HT & TC interrupts
	DMA1_Channel1->CCR |= DMA_CCR_HTIE | DMA_CCR_TCIE;

	// Enable DMA1 Channel 1
	DMA1_Channel1->CCR |= DMA_CCR_EN;

	// Enable ADC DMA Request in circular mode
	ADC1->CFGR1 |= ADC_CFGR1_DMACFG | ADC_CFGR1_DMAEN;

	// Enable ADC and wait until ready
	ADC1->CR |= ADC_CR_ADEN;
	while ((ADC1->ISR & ADC_ISR_ADRDY) == 0);

	// Start conversion (waits for TIM3 triggers)
	ADC1->CR |= ADC_CR_ADSTART;
}


/*
 * BSP_ADC_Resync()
 * Restarts the ADC scan and the DMA at the start of the buffer, so that each
 * scan is stored again in channel order. Called after an ADC overrun or when
 * the last slot of a scan does not hold the internal reference.
 */

void BSP_ADC_Resync()
{
	// Stop the conversions
	ADC1->CR |= ADC_CR_ADSTP;
	while ((ADC1->CR & ADC_CR_ADSTP) == ADC_CR_ADSTP);

	// Restart the DMA at the start of the buffer
	DMA1_Channel1->CCR &= ~DMA_CCR_EN;
	DMA1_Channel1->CNDTR = 2*ADC_NB_CHANNELS;
	DMA1->IFCR = DMA_IFCR_CGIF1;

	// Clear the ADC flags and wait for the next TIM3 trigger
	ADC1->ISR = ADC_ISR_OVR | ADC_ISR_EOSEQ | ADC_ISR_EOC;
	DMA1_Channel1->CCR |= DMA_CCR_EN;
	ADC1->CR |= ADC_CR_ADSTART;
}







/*
 * BSP_TIMER_Timebase_Init()
 * TIM6 at 48MHz
 * Prescaler   = 48000 -> Counting period = 1ms
 * Auto-reload = 500   -> Update period   = 500ms
 */

void BSP_TIMER_Timebase_Init()
{
	// Enable TIM6 clock
	RCC->APB1ENR |= RCC_APB1ENR_TIM6EN;

	// Reset TIM6 configuration
	TIM6->CR1 = 0x0000;
	TIM6->CR2 = 0x0000;

	// Set TIM6 prescaler
	// Fck = 48MHz -> /48000 = 1KHz counting frequency
	TIM6->PSC = (uint16_t) 48000 -1;

	// Set TIM6 auto-reload register for 500ms
	TIM6->ARR = (uint16_t) 500 -1;

	// Enable auto-reload preload
	TIM6->CR1 |= TIM_CR1_ARPE;

	// Enable Interrupt upon Update Event
	TIM6->DIER |= TIM_DIER_UIE;

	// Start TIM6 counter
	TIM6->CR1 |= TIM_CR1_CEN;
}

/*
 * BSP_TIMER_Trigger_Init()
 * TIM3 at 48MHz, triggers the ADC scans
 * Prescaler   = 48  -> Counting period = 1us
 * Auto-reload = 500 -> Update period   = 500us (2kHz sampling)
 * Update event sent on TRGO
 */

void BSP_TIMER_Trigger_Init()
{
	// Enable TIM3 clock
	RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;

	// Reset TIM3 configuration
	TIM3->CR1 = 0x0000;
	TIM3->CR2 = 0x0000;

	// Set TIM3 prescaler
	// Fck = 48MHz -> /48 = 1MHz counting frequency
	TIM3->PSC = (uint16_t) 48 -1;

	// Set TIM3 auto-reload register for 500us
	TIM3->ARR = (uint16_t) 500 -1;

	// Enable auto-reload preload
	TIM3->CR1 |= TIM_CR1_ARPE;

	// Master mode: update event as trigger output (MMS = 010)
	TIM3->CR2 |= (0x02 <<TIM_CR2_MMS_Pos);

	// Start TIM3 counter
	TIM3->CR1 |= TIM_CR1_CEN;
}

/*
 * BSP_TIMER_IC_Init()
 * TIM3 as Input Capture
 * Channel 1 -> PB4 (AF1)
 */

void BSP_TIMER_IC_Init()
{
	// Enable GPIOB clock
	RCC->AHBENR |= RCC_AHBENR_GPIOBEN;

	// Configure PB4 as Alternate function
	GPIOB->MODER &= ~(GPIO_MODER_MODER4_Msk);
	GPIOB->MODER |=  (0x02 <<GPIO_MODER_MODER4_Pos);

	// Set PB4 to AF1 (TIM3_CH1)
	GPIOB->AFR[0] &= ~(0x000F0000);
	GPIOB->AFR[0] |=  (0x00010000);

	// Enable TIM3 clock
	RCC -> APB1ENR |= RCC_APB1ENR_TIM3EN;

	// Reset TIM3 configuration
	TIM3->CR1  = 0x0000;
	TIM3->CR2  = 0x0000;
	TIM3->CCER = 0x0000;

	// Set TIM3 prescaler
	// Fck = 48MHz -> /48000 = 1KHz counting frequency
	TIM3->PSC = (uint16_t) 48000 -1;

	// Set Auto-Reload to maximum value
	TIM3->ARR = (uint16_t) 0xFFFF;

	// Reset Input Capture configuration
	TIM3->CCMR1 = 0x0000;
	TIM3->CCMR2 = 0x0000;

	// Set Channel 1 input on TI1
	TIM3->CCMR1 |= (0x01 <<TIM_CCMR1_CC1S_Pos);

	// Filter with N=8
	TIM3->CCMR1 |= (0x03 <<TIM_CCMR1_IC1F_Pos);

	// Select falling edge for channel 1
	TIM3->CCER |= (0x00 <<TIM_CCER_CC1NP_Pos) | (0x01 <<TIM_CCER_CC1P_Pos);

	// Enable capture on channel 1
	TIM3->CCER |= (0x01 <<TIM_CCER_CC1E_Pos);

	// Enable TIM3
	TIM3->CR1 |= TIM_CR1_CEN;

	// Setup Input Capture
		TIM3->CCMR1 = 0x0000;
		TIM3->CCMR2 = 0x0000;

		// Channel 1 input on TI1
		TIM3->CCMR1 |= (0x01 <<TIM_CCMR1_CC1S_Pos);

		// Channel 2 input also on TI1
		TIM3->CCMR1 |= (0x02 <<TIM_CCMR1_CC2S_Pos);

		// Filter with N=8
		TIM3->CCMR1 |= (0x03 <<TIM_CCMR1_IC1F_Pos) | (0x03 <<TIM_CCMR1_IC2F_Pos);

		// Select falling edge for channel 1
		TIM3->CCER |= (0x00 <<TIM_CCER_CC1NP_Pos) | (0x01 <<TIM_CCER_CC1P_Pos);

		// Select rising edge for channel 2
		TIM3->CCER |= (0x00 <<TIM_CCER_CC2NP_Pos) | (0x00 <<TIM_CCER_CC2P_Pos);

		// Enable capture on channel 1 & channel 2
		TIM3->CCER |= (0x01 <<TIM_CCER_CC1E_Pos) | (0x01 <<TIM_CCER_CC2E_Pos);

		// Choose Channel 1 as trigger input
		TIM3->SMCR |= (0x05 <<TIM_SMCR_TS_Pos);

		// Slave mode -> Resets counter when trigger occurs
		TIM3->SMCR |= (0x4 <<TIM_SMCR_SMS_Pos);

		// Enable TIM3
		TIM3->CR1 |= TIM_CR1_CEN;
}

/*
 * BSP_TIMER_PWM_Init()
 * TIM1 as Output Compare PWM mode
 * Channel 1 -> PA8 (AF2)
 * Channel 2 -> PA9 (AF2)
 */

void BSP_TIMER_PWM_Init()
{
	// Enable GPIOA clock
	RCC->AHBENR |= RCC_AHBENR_GPIOAEN;

	// Configure PA8 and PA9 as Alternate Function
	GPIOA->MODER &= ~(GPIO_MODER_MODER8_Msk | GPIO_MODER_MODER9_Msk);
	GPIOA->MODER |=  (0x02 <<GPIO_MODER_MODER8_Pos) | (0x02 <<GPIO_MODER_MODER9_Pos);

	// Set PA8 and PA9 to AF2 (TIM1)
	GPIOA->AFR[1] &= ~(0x000000FF);
	GPIOA->AFR[1] |=  (0x00000022);

	// Enable TIM1 clock
	RCC -> APB2ENR |= RCC_APB2ENR_TIM1EN;

	// Reset TIM1 configuration
	TIM1->CR1  = 0x0000;
	TIM1->CR2  = 0x0000;
	TIM1->CCER = 0x0000;

	// Set TIM1 prescaler
	// Fck = 48MHz -> /48 = 1MHz counting frequency (1µs resolution)
	TIM1->PSC = (uint16_t) 48 -1;

	// Set Auto-Reload to period = 11ms
	TIM1->ARR = (uint16_t) 11000;

	// Enable Auto-Reload Preload register
	TIM1->CR1 |= TIM_CR1_ARPE;

	// Setup Input Capture
	TIM1->CCMR1 = 0x0000;
	TIM1->CCMR2 = 0x0000;

	// Setup PWM mode 1 output
	TIM1->CCMR1 |= (0x06 <<TIM_CCMR1_OC1M_Pos) | TIM_CCMR1_OC1PE;
	TIM1->CCMR1 |= (0x06 <<TIM_CCMR1_OC2M_Pos) | TIM_CCMR1_OC2PE;

	// Set default PWM values
	TIM1->CCR1 = 1500;
	TIM1->CCR2 = 1500;

	// Enable Outputs
	TIM1->CCER |= TIM_CCER_CC1E | TIM_CCER_CC2E;

	// Enable Main output
	TIM1->BDTR |= TIM_BDTR_MOE;

	// Enable TIM1
	TIM1->CR1 |= TIM_CR1_CEN;
}

/*
 * DAC_Init()
 * Initialize DAC for a single output
 * on channel 1 -> pin PA4
 */

void BSP_DAC_Init()
{
	// Enable GPIOA clock
	RCC->AHBENR |= RCC_AHBENR_GPIOAEN;

	// Configure pin PA4 as analog
	GPIOA->MODER &= ~GPIO_MODER_MODER4_Msk;
	GPIOA->MODER |= (0x03 <<GPIO_MODER_MODER4_Pos);

	// Enable DAC clock
	RCC->APB1ENR |= RCC_APB1ENR_DACEN;

	// Reset DAC configuration
	DAC->CR = 0x00000000;

	// Enable DAC Channel 1
	DAC->CR |= DAC_CR_EN1;
}



/*
 * BSP_NVIC_Init()
 * Setup NVIC controller for desired interrupts
 */

void BSP_NVIC_Init()
{
	// Set maximum priority for DMA1_Channel1 (ADC scans) interrupts
	NVIC_SetPriority(DMA1_Channel1_IRQn, 0);

	// Enable DMA1_Channel1 interrupts
	NVIC_EnableIRQ(DMA1_Channel1_IRQn);

	// Set priority level 1 for TIM6 interrupt
	NVIC_SetPriority(TIM6_DAC_IRQn, 1);

	// Enable TIM6 interrupts
	NVIC_EnableIRQ(TIM6_DAC_IRQn);
}


/*
 * BSP_I2C1_Init()
 * Initialize I2C1 peripheral @100kHz
 */

void BSP_I2C1_Init()
{
	// Pin configuration for I2C2 pins
	// SCL -> PB8
	// SDA -> PB9
	// Enable GPIOB clock
	RCC->AHBENR |= RCC_AHBENR_GPIOBEN;

	// Configure PB8, PB9 as AF mode
	GPIOB->MODER &= ~(GPIO_MODER_MODER8 | GPIO_MODER_MODER9);
	GPIOB->MODER |= (0x02 <<16U) | (0x02 <<18U);

	// Connect to I2C1 (AF1)
	GPIOB->AFR[1] &= ~(0x000000FF);
	GPIOB->AFR[1] |=   0x00000011;

	// Setup Open-Drain
	GPIOB->OTYPER |= GPIO_OTYPER_OT_8 | GPIO_OTYPER_OT_9;

	// Select SYSCLK as I2C1 clock (48MHz)
	RCC->CFGR3 |= RCC_CFGR3_I2C1SW;

	// Enable I2C1 clock
	RCC->APB1ENR |= RCC_APB1ENR_I2C1EN;

	// Make sure I2C1 is disabled
	I2C1->CR1 &= ~I2C_CR1_PE;

	// Reset I2C1 Configuration to default values
	I2C1->CR1 	  = 0x00000000;
	I2C1->CR2 	  = 0x00000000;
	I2C1->TIMINGR = 0x00000000;

	// Configure timing for 100kHz, 50% duty cycle
	I2C1->TIMINGR |= ((4 -1) <<I2C_TIMINGR_PRESC_Pos); // Clock prescaler /4 -> 12MHz
	I2C1->TIMINGR |= (60 	 <<I2C_TIMINGR_SCLH_Pos);  // High half-period = 5µs
	I2C1->TIMINGR |= (60     <<I2C_TIMINGR_SCLL_Pos);  // Low  half-period = 5µs

	// Enable I2C1
	I2C1->CR1 |= I2C_CR1_PE;
}

void BSP_DBG_Pins_Init()
{
	//Enable clock on GPIOA
	RCC->AHBENR |= RCC_AHBENR_GPIOAEN;

	//Enable clock on GPIOC
	RCC->AHBENR |= RCC_AHBENR_GPIOCEN;


	//Configure PA0 as output mode
	GPIOA->MODER &= ~(GPIO_MODER_MODER0_Msk);
	GPIOA->MODER |= 0x01 << GPIO_MODER_MODER0_Pos;
	//Configure PA0 as a push-pull output
	GPIOA->OTYPER &= ~(GPIO_OTYPER_OT_0);


	//Configure PA4 as output mode
	GPIOA->MODER &= ~(GPIO_MODER_MODER4_Msk);
	GPIOA->MODER |= 0x01 << GPIO_MODER_MODER4_Pos;
	//Configure PA4 as a push-pull output
	GPIOA->OTYPER &= ~(GPIO_OTYPER_OT_4);

	//Configure PC1 as output mode
	GPIOC->MODER &= ~(GPIO_MODER_MODER1_Msk);
	GPIOC->MODER |= 0x01 << GPIO_MODER_MODER1_Pos;
	//Configure PA4 as a push-pull output
	GPIOC->OTYPER &= ~(GPIO_OTYPER_OT_1);

}

uint8_t	BSP_I2C1_Read( uint8_t device_address,
                       uint8_t register_address,
                       uint8_t *buffer,
                       uint8_t nbytes )
{
	uint32_t 	timeout;	// Flag waiting timeout
	uint8_t		n;			// Loop counter

	// Set device address
	I2C1->CR2 &= ~I2C_CR2_SADD_Msk;
	I2C1->CR2 |= ((device_address <<1U) <<I2C_CR2_SADD_Pos);

	// Set I2C in Write mode
	I2C1->CR2 &= ~I2C_CR2_RD_WRN;

	// Transfer NBYTES = 1, no AUTOEND
	I2C1->CR2 &= ~I2C_CR2_NBYTES;
	I2C1->CR2 |= (1 <<16U);
	I2C1->CR2 &= ~I2C_CR2_AUTOEND;

	// Start I2C transaction
	I2C1->CR2 |= I2C_CR2_START;

	// Wait for TXIS with timeout
	timeout = 100000;
	while (((I2C1->ISR) & I2C_ISR_TXIS) != I2C_ISR_TXIS)
	{
		timeout--;
		if (timeout == 0) return 1;
	}

	// Send Register address
	I2C1->TXDR = register_address;

	// Wait for TC with timeout
	timeout = 100000;
	while (((I2C1->ISR) & I2C_ISR_TC) != I2C_ISR_TC)
	{
		timeout--;
		if (timeout == 0) return 2;
	}

	// Set I2C in Read mode
	I2C1->CR2 |= I2C_CR2_RD_WRN;

	// Transfer NBYTES, no AUTOEND
	I2C1->CR2 &= ~I2C_CR2_NBYTES;
	I2C1->CR2 |= (nbytes <<16U);
	I2C1->CR2 &= ~I2C_CR2_AUTOEND;

	// Re-Start transaction
	I2C1->CR2 |= I2C_CR2_START;

	n = nbytes;
	while (n>0)
	{
		// Wait for RXNE with timeout
		timeout = 100000;
		while (((I2C1->ISR) & I2C_ISR_RXNE) != I2C_ISR_RXNE)
		{
			timeout--;
			if (timeout == 0) return 3;
		}

		// Store data into buffer
		*buffer = I2C1->RXDR;
		buffer++;
		n--;
	}

	// Generate STOP condition
	I2C1->CR2 |= I2C_CR2_STOP;

	// Wait for STOPF with timeout
	timeout = 100000;
	while (((I2C1->ISR) & I2C_ISR_STOPF) != I2C_ISR_STOPF)
	{
		timeout--;
		if (timeout == 0) return 4;
	}

	// Return success
	return 0;
}

uint8_t	BSP_I2C1_Write( uint8_t device_address,
                        uint8_t register_address,
                        uint8_t *buffer, uint8_t nbytes )
{
	uint32_t 	timeout;	// Flag waiting timeout
	uint8_t		n;			// Loop counter

	// Set device address
	I2C1->CR2 &= ~I2C_CR2_SADD_Msk;
	I2C1->CR2 |= ((device_address <<1U) <<I2C_CR2_SADD_Pos);

	// Set I2C in Write mode
	I2C1->CR2 &= ~I2C_CR2_RD_WRN;

	// Transfer NBYTES, with AUTOEND
	I2C1->CR2 &= ~I2C_CR2_NBYTES;
	I2C1->CR2 |= ((nbytes+1) <<16U);
	I2C1->CR2 |= I2C_CR2_AUTOEND;

	// Clear STOPF flag
	I2C1->ICR |= I2C_ICR_STOPCF;

	// Start I2C transaction
	I2C1->CR2 |= I2C_CR2_START;

	// Wait for TXIS with timeout
	timeout = 100000;
	while (((I2C1->ISR) & I2C_ISR_TXIS) != I2C_ISR_TXIS)
	{
		timeout--;
		if (timeout == 0) return 1;
	}

	// Send register address
	I2C1->TXDR = register_address;

	n = nbytes;
	while(n>0)
	{
		// Wait for TXIS with timeout
		timeout = 100000;
		while (((I2C1->ISR) & I2C_ISR_TXIS) != I2C_ISR_TXIS)
		{
			timeout--;
			if (timeout == 0) return 2;
		}

		// Send data
		I2C1->TXDR = *buffer;
		buffer++;
		n--;
	}

	// Wait for STOPF with timeout
	timeout = 100000;
	while (((I2C1->ISR) & I2C_ISR_STOPF) != I2C_ISR_STOPF)
	{
		timeout--;
		if (timeout == 0) return 3;
	}

	// Return success
	return 0;
}

/*
 * BSP_SPI1_Init()
 * Initialize SPI1 peripheral @375kHz
 */

void BSP_SPI1_Init()
{
	// SPI_SCK  -> PB3 (AF0)
	// SPI_MISO -> PB4 (AF0)
	// SPI_MOSI -> PB5 (AF0)
	// CS pin	-> PC7 (GPIO)

	// Configure PC7 as CS pin

	// Enable GPIOC clock
	RCC->AHBENR |= RCC_AHBENR_GPIOCEN;

	// Configure PC7 as output
	GPIOC->MODER &= ~GPIO_MODER_MODER7_Msk;
	GPIOC->MODER |= (0x01 <<GPIO_MODER_MODER7_Pos);

	// Configure PC7 as Push-Pull output
	GPIOC->OTYPER &= ~GPIO_OTYPER_OT_7;

	// Configure PC7 as High-Speed Output
	GPIOC->OSPEEDR &= ~GPIO_OSPEEDR_OSPEEDR7_Msk;
	GPIOC->OSPEEDR |= (0x03 <<GPIO_OSPEEDR_OSPEEDR7_Pos);

	// Disable PC7 Pull-up/Pull-down
	GPIOC->PUPDR &= ~GPIO_PUPDR_PUPDR7_Msk;

	// Idle state is high
	GPIOC->BSRR = GPIO_BSRR_BS_7;

	// Configure PB3, PB5, PB5 as SPI1 pins (AF0)

	// Enable GPIOB clock
	RCC->AHBENR |= RCC_AHBENR_GPIOBEN;

	// Configure PB3, PB4, PB5 as AF mode
	GPIOB->MODER &= ~(GPIO_MODER_MODER3 | GPIO_MODER_MODER4 | GPIO_MODER_MODER5);
	GPIOB->MODER |= (0x02 <<6U) |(0x02 <<8U) |(0x02 <<10U);

	// Connect to SPI1 (AF0)
	GPIOB->AFR[0] &= ~(0x00FFF000);
	GPIOB->AFR[0] |=  (0x00000000);

	// Enable SPI1 Clock
	RCC->APB2ENR |= RCC_APB2ENR_SPI1EN;

	// Configure SPI with default config
	// 4-wire = full-duplex (MISO/MOSI on separated lines)
	// 8-bit, no CRC, MSB first
	// CPHA = 0, CPOL = 0 -> SPI mode 0 (first clock rising edge)
	SPI1->CR1 = 0x0000;
	SPI1->CR2 = 0x0000;

	// Set the baudrate to 48MHz /128 = 375kHz (slow, but easy to debug)
	SPI1->CR1 |= 0x06 <<SPI_CR1_BR_Pos;

	// Set data size to 8-bit
	SPI1->CR2 |= 0x07 <<SPI_CR2_DS_Pos;

	// Set as master (SSI must be high), with software managed NSS
	SPI1->CR1 |= SPI_CR1_MSTR | SPI_CR1_SSI | SPI_CR1_SSM;

	// Enable SPI1
	SPI1->CR1 |= SPI_CR1_SPE;
}

uint8_t BSP_SPI_SendReceive(uint8_t tx_byte)
{
	uint8_t	rx_byte;
	// Make sure TXE is set before sending data
	while((SPI1->SR & SPI_SR_TXE_Msk) == 0);

	// Send tx_byte
	*(__IO uint8_t *)&SPI1->DR = tx_byte;

	// Wait until incoming data has arrived
	while((SPI1->SR & SPI_SR_RXNE_Msk) == 0);

	// Read data
	rx_byte = *(__IO uint8_t *)&SPI1->DR;

	return rx_byte;
}

void BSP_LPS25H_Read(uint8_t register_address, uint8_t *buffer, uint8_t nbytes)
{
	uint8_t		ms_bit_msk;
	uint8_t		n;

	// Set the M/S bit depending on the number of byte to read
	if(nbytes > 1) 	ms_bit_msk = 0x40;    // bit-6 mask
	else		ms_bit_msk = 0x00;

	// Set FIFO threshold to 1-byte
	SPI1->CR2 |= SPI_CR2_FRXTH;

	// Select slave (CS -> low)
	GPIOC->BSRR = GPIO_BSRR_BR_7;

	// Send register address to read from
	BSP_SPI_SendReceive(register_address | 0x80 | ms_bit_msk);

	// Read loop
	n = nbytes;

	while(n>0)
	{
		*buffer = BSP_SPI_SendReceive(0x00);
		buffer++;
		n--;
	}

	// Release slave (CS -> High)
	GPIOC->BSRR = GPIO_BSRR_BS_7;
}

void BSP_LPS25H_Write(uint8_t register_address, uint8_t data)
{
	// Set FIFO threshold to 1-byte
	SPI1->CR2 |= SPI_CR2_FRXTH;

	// Select slave (CS -> low)
	GPIOC->BSRR = GPIO_BSRR_BR_7;

	// Send register address to write to
	BSP_SPI_SendReceive(register_address);

	// Send data to write
	BSP_SPI_SendReceive(data);

	// Release slave (CS -> High)
	GPIOC->BSRR = GPIO_BSRR_BS_7;
}

