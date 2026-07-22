package com.vbnx.planewar.game

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import kotlin.random.Random

/** 三层视差星空背景 */
class StarField(private val width: Float, private val height: Float) {

    private class Star(var x: Float, var y: Float, val speed: Float, val size: Float, val shade: Int)

    private val stars = ArrayList<Star>()

    init {
        for (i in 0 until 90) {
            val layer = Random.nextInt(3)
            stars.add(
                Star(
                    x = Random.nextFloat() * width,
                    y = Random.nextFloat() * height,
                    speed = when (layer) { 0 -> 60f; 1 -> 140f; else -> 260f },
                    size = when (layer) { 0 -> 2f; 1 -> 3.5f; else -> 5f },
                    shade = when (layer) { 0 -> 90; 1 -> 160; else -> 235 }
                )
            )
        }
    }

    fun update(dt: Float) {
        for (s in stars) {
            s.y += s.speed * dt
            if (s.y > height) {
                s.y = -4f
                s.x = Random.nextFloat() * width
            }
        }
    }

    fun draw(canvas: Canvas, paint: Paint) {
        paint.style = Paint.Style.FILL
        for (s in stars) {
            paint.color = Color.rgb(s.shade, s.shade, s.shade)
            canvas.drawCircle(s.x, s.y, s.size, paint)
        }
    }
}
