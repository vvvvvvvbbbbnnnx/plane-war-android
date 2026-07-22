package com.vbnx.planewar.game

import android.graphics.Canvas
import android.graphics.Paint
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/** 爆炸粒子效果 */
class Explosion(x: Float, y: Float, baseColor: Int) {

    private class Particle(
        var x: Float, var y: Float,
        val vx: Float, val vy: Float,
        val size: Float, val color: Int,
        var life: Float
    )

    private val particles = ArrayList<Particle>()
    private val maxLife = 0.55f

    init {
        val count = 22
        for (i in 0 until count) {
            val angle = Random.nextFloat() * 2f * Math.PI.toFloat()
            val speed = 120f + Random.nextFloat() * 420f
            particles.add(
                Particle(
                    x = x, y = y,
                    vx = cos(angle) * speed,
                    vy = sin(angle) * speed,
                    size = 4f + Random.nextFloat() * 10f,
                    color = if (Random.nextBoolean()) baseColor else 0xFFFFD54F.toInt(),
                    life = maxLife * (0.6f + Random.nextFloat() * 0.4f)
                )
            )
        }
    }

    val isFinished: Boolean
        get() = particles.all { it.life <= 0f }

    fun update(dt: Float) {
        for (p in particles) {
            if (p.life <= 0f) continue
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
        }
    }

    fun draw(canvas: Canvas, paint: Paint) {
        paint.style = Paint.Style.FILL
        for (p in particles) {
            if (p.life <= 0f) continue
            val alpha = ((p.life / maxLife) * 255).toInt().coerceIn(0, 255)
            paint.color = p.color
            paint.alpha = alpha
            canvas.drawCircle(p.x, p.y, p.size * (p.life / maxLife), paint)
        }
        paint.alpha = 255
    }
}
