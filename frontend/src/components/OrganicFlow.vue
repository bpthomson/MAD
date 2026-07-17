<template>
  <canvas ref="canvasRef" id="canvas-background"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)
let animationId = null

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  let particles = []
  const particleCount = 60
  const connectionDistance = 150
  const flowSpeed = 0.3

  const onResize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  window.addEventListener('resize', onResize)

  class Particle {
    constructor() {
      this.x = Math.random() * canvas.width
      this.y = Math.random() * canvas.height
      this.size = Math.random() * 1.5 + 0.5
      this.baseSpeedX = Math.random() * flowSpeed + 0.1
      this.baseSpeedY = -(Math.random() * flowSpeed + 0.1)
      this.angle = Math.random() * Math.PI * 2
      this.angleSpeed = Math.random() * 0.02
    }
    update() {
      this.x += this.baseSpeedX + Math.sin(this.angle) * 0.2
      this.y += this.baseSpeedY + Math.cos(this.angle) * 0.2
      this.angle += this.angleSpeed
      if (this.x > canvas.width + 50) this.x = -50
      if (this.x < -50) this.x = canvas.width + 50
      if (this.y < -50) this.y = canvas.height + 50
      if (this.y > canvas.height + 50) this.y = -50
    }
    draw() {
      ctx.fillStyle = 'rgba(74, 64, 54, 0.4)'
      ctx.beginPath()
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle())
  }

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    for (let i = 0; i < particles.length; i++) {
      particles[i].update()
      particles[i].draw()
      for (let j = i; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const distance = Math.sqrt(dx * dx + dy * dy)
        if (distance < connectionDistance) {
          const opacity = (1 - distance / connectionDistance) * 0.08
          ctx.strokeStyle = `rgba(74, 64, 54, ${opacity})`
          ctx.lineWidth = 0.8
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.stroke()
        }
      }
    }
    animationId = requestAnimationFrame(animate)
  }
  animate()

  // Store cleanup ref
  canvasRef.value._cleanup = () => {
    window.removeEventListener('resize', onResize)
  }
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (canvasRef.value?._cleanup) canvasRef.value._cleanup()
})
</script>
