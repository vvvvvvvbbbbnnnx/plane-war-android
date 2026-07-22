package com.vbnx.planewar.game

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint

/** 子弹：friendly=true 为玩家子弹，否则为敌机子弹 */
class Bullet(
    var x: Float,
    var y: Float,
    val vx: Float,
    val vy: Float,
    val friendly: Boolean,
    val damage: Int = 1
) {
    val radius = if (friendly) 7f else 11f

    fun update(dt: Float) {
        x += vx * dt
        y += vy * dt
    }

    fun isOffScreen(width: Float, height: Float): Boolean =
        y < -40f || y > height + 40f || x < -40f || x > width + 40f

    fun draw(canvas: Canvas, paint: Paint) {
        paint.style = Paint.Style.FILL
        if (friendly) {
            paint.color = Color.parseColor("#FFEE58")
            canvas.drawRect(x - radius / 2, y - radius * 2.2f, x + radius / 2, y + radius * 0.6f, paint)
        } else {
            paint.color = Color.parseColor("#FF1744")
            canvas.drawCircle(x, y, radius, paint)
        }
    }
}
